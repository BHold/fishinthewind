import datetime
import os
import zipfile
from cStringIO import StringIO

from django.db import models
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from PIL import Image
from boto.s3.connection import S3Connection, SubdomainCallingFormat
from boto.exception import S3ResponseError
from sorl.thumbnail import ImageField
from django.conf import settings

# Used to store gallery .zipfiles locally, instead of at MEDIA_ROOT since there
# is no need to send them to S3
fs = FileSystemStorage(location='%s/../blog_wind/' % settings.PROJECT_ROOT)


class CommonManager(models.Manager):
    """
    Manager for Posts, Galleries, and Photos

    Provides functions to filter for objects that are active
    and/or should be currently posted
    """
    def get_active(self): 
        return self.get_query_set().filter(active=True)

    def get_posted(self):
        return self.get_query_set().filter(publish_at__lte=datetime.datetime.now(), active=True)


class CommonInfo(models.Model):
    """
    Abstract model for Post, Gallery, and Photo that provides common fields
    """
    title = models.CharField(max_length=120,
                             help_text="Can be up to 120 characters.")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True,
                    help_text="Controls whether or not object is live to world")
    objects = CommonManager()

    class Meta:
        abstract = True


class Photo(CommonInfo):
    image = ImageField(upload_to="galleries/photos/%Y/%m/%d")
    height = models.PositiveIntegerField(blank=True, null=True)
    width = models.PositiveIntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ['title']

    def delete(self, *args, **kwargs):
        """
        Deletes the photo off of s3 before instance of Photo is deleted
        """
        try:
            path = self.image.path
            os.remove(path)
        except NotImplementedError: # This is live server, where images are on S3, and thus no absolute file path
            conn = S3Connection(settings.AWS_ACCESS_KEY_ID, settings.AWS_SECRET_ACCESS_KEY, calling_format=SubdomainCallingFormat())
            try:
                bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME)
                bucket.delete_key(self.image.name)
            except S3ResponseError:  # bucket doesn't exist for some reason
                pass
        super(Photo, self).delete(*args, **kwargs)


class Gallery(CommonInfo):
    photos = models.ManyToManyField(Photo, related_name='galleries', null=True, blank=True)

    def __unicode__(self):
        return self.title

    def delete(self, *args, **kwargs):
        """
        Deletes the photos that are only associated with this gallery
        """
        for photo in self.photos.all():
            if photo.galleries.count() == 1:
                photo.delete()
        super(Gallery, self).delete(*args, **kwargs)


class Post(CommonInfo):
    slug = models.SlugField(unique=True)
    body = models.TextField(blank=True, help_text="Main body text for post. Can use html tags. Paragraph tags will be used automatically before/after open line")
    publish_at = models.DateTimeField(default=datetime.datetime.now(),
                                      help_text="Date and time post should become active.")
    gallery = models.ForeignKey(Gallery, related_name="post", blank=True, null=True)

    def __unicode__(self):
        return self.title

    @models.permalink
    def get_absolute_url(self):
        return('post', (), {
            'slug': self.slug
        })

    class Meta:
        ordering = ['-publish_at', '-modified', '-created']


class GalleryUpload(models.Model):
    """
    Used to easily create Galleries in admin section

    Provided a .zip file of photos it creates a gallery
    """
    zip_file = models.FileField(upload_to='temp', storage=fs, help_text="Select a .zip file of images to upload")
    gallery = models.ForeignKey(Gallery, null=True, blank=True,
                            help_text="Select a gallery to add these images to. Leave blank to create new gallery.")
    title = models.CharField(max_length=120,
                             help_text="Can be up to 120 characters.")

    def save(self, *args, **kwargs):
        super(GalleryUpload, self).save(*args, **kwargs)
        self.process_zipfile()
        self.delete()

    def process_zipfile(self):
        if os.path.isfile(self.zip_file.path):
            zf = zipfile.ZipFile(self.zip_file.path)
            bad_file = zf.testzip()
            if bad_file:
                raise Exception('"%s" in the .zip file is corrupt.' % bad_file)
            if self.gallery:
                gallery = self.gallery
            else:
                gallery = Gallery.objects.create(title=self.title)
            count = 1
            for filename in sorted(zf.namelist()):
                if filename.startswith('__'):  # don't process meta files
                    continue
                data = zf.read(filename)
                if len(data):
                    img_file = StringIO(data)
                    try:
                        # load() can spot a truncated JPEG
                        trial_image = Image.open(img_file)
                        trial_image.load()

                        # Since we're about to use the file again we have to reset the
                        # file object if possible.
                        if hasattr(img_file, 'reset'):
                            img_file.reset()

                        # verify() can spot a corrupt PNG
                        # but it must be called immediately after the constructor
                        trial_image = Image.open(img_file)
                        trial_image.verify()
                    except Exception: # PIL doesn't recognize file as an image, so we skip it
                        continue

                    title = self.title + ' ' + str(count).zfill(2)
                    try:
                        photo = Photo.objects.get(title=title)
                    except Photo.DoesNotExist:
                        photo = Photo.objects.create(title=title)
                        photo.width = trial_image.size[0]
                        photo.height = trial_image.size[1]
                        photo.image.save(filename, ContentFile(data))
                        gallery.photos.add(photo)
                    count += 1
            zf.close()

    def delete(self, *args, **kwargs):
        """
        Deletes the zip file used to create the gallery since it is no longer needed 
        """
        os.remove(self.zip_file.path)
        super(GalleryUpload, self).delete(*args, **kwargs)
