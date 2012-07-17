import datetime
import os
import zipfile
from cStringIO import StringIO

from django.db import models
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from PIL import Image
from storages.backends.s3boto import S3BotoStorage

# Used to store gallery .zipfiles locally, instead of at MEDIA_ROOT since there is no need to send them to S3
#fs = FileSystemStorage(location='/temp')

class CommonManager(models.Manager):
    """
    Manager for Posts, Galleries, and Photos

    Provides functions to filter for objects that are active and/or should be currently posted
    """
    def get_active(self):
        return self.get_query_set().filter(active=True)
    
    def get_posted(self):
        return self.get_query_set().filter(publish_at__lte=datetime.datetime.now(), active=True)

class CommonInfo(models.Model):
    """
    Abstract model for Post, Gallery, and Photo that provides 
    'title', 'created', 'modified', and 'active' fields.
    Also sets manager to CommonManager.
    """
    title = models.CharField(max_length=120,
                             help_text="Can be up to 120 characters.")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True,
                                 help_text="Controls whether or not object is live to the world")
    objects = CommonManager()

    class Meta:
        abstract = True

class Post(CommonInfo):
    slug = models.SlugField(unique=True)
    body = models.TextField(help_text="Main body text for post. Can use html tags. Paragraph tags will be used automatically before/after open line")
    publish_at = models.DateTimeField(default=datetime.datetime.now(),
                                      help_text="Date and time post should become active.")
    is_gallery = models.BooleanField(default=False)

    def __unicode__(self):
        return self.title
        

    @models.permalink
    def get_absolute_url(self):
        return('post', (), {
            'slug': self.slug
        })

    class Meta:
        ordering = ['-publish_at', '-modified', '-created']

class Gallery(CommonInfo):
    photos = models.ManyToManyField(Photo, related_name='galleries', null=True, blank=True)

class Photo(CommonInfo):
    image = models.ImageField(upload_to="galleries/photos/%Y/%m/%d",
                                storage=S3BotoStorage)

class GalleryUpload(models.Model):
    zip_file = models.FileField(label="Images File (.zip)", upload_to='temp',
                            help_text="Select a .zip file of images to upload")
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
            for filename in zf.namelist():
                if filename.startswith('__'): # don't process meta files
                    continue
                data = zf.read(filename)
                if len(data):
                    try:
                        # the following is from django.forms.fields.ImageField:
                        # load() is the only method that can spot a truncated JPEG,
                        #  but it cannot be called sanely after verify()
                        trial_image = Image.open(file)
                        trial_image.load()

                        # Since we're about to use the file again we have to reset the
                        # file object if possible.
                        if hasattr(file, 'reset'):
                            file.reset()

                        # verify() is the only method that can spot a corrupt PNG,
                        #  but it must be called immediately after the constructor
                        trial_image = Image.open(file)
                        trial_image.verify()
                    except Exception: # PIL doesn't recognize file as an image, so we skip it
                        continue

                    title = self.title + ' ' + str(count)
                    try:
                        photo = Photo.objects.get(title=title)
                    except Photo.DoesNotExist:
                        photo = Photo(title=title)
                        photo.image.save(filename, ContentFile(data))
                        gallery.photos.add(photo)
                    count += 1
            zf.close()



