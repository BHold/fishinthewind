import datetime
import os
import zipfile
from cStringIO import StringIO

from boto.exception import S3ResponseError
from boto.s3.connection import S3Connection, SubdomainCallingFormat
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image
from pygments import highlight
from pygments import lexers
from pygments.formatters import HtmlFormatter
from sorl.thumbnail import ImageField

body_help_text = """
                 Main body text for post.

                 Can use html tags. Should put paragraphs inside p tags: &lt;p&gt;(text here)&lt;p&gt;.
                 Links should have class 'article-link' for proper styling.

                 Inline code (shell commands, paths, etc.) should be wrapped in &lt;code&gt; elements.
                 Code inside &lt;pre&gt; elements will be syntax hightlighted.
                 &lt;pre&gt; tags should have a class name of the language of the code (ie 'python', 'javascript').

                 Text will not be autoescaped on page!
                 """


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

    class Meta:
        ordering = ['title']

    def __unicode__(self):
        return self.title

    def delete(self, *args, **kwargs):
        """
        Deletes the photo off of s3 before instance of Photo is deleted
        """
        try:
            path = self.image.path
            os.remove(path)
        except NotImplementedError:  # This is live server, where images are on S3, and thus no absolute file path
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
    body = models.TextField(blank=True, help_text=body_help_text)
    body_highlighted = models.TextField(blank=True)
    publish_at = models.DateTimeField(default=datetime.datetime.now(),
                                      help_text="Date and time post should become active.")
    gallery = models.ForeignKey(Gallery, related_name="post", blank=True, null=True)

    class Meta:
        ordering = ['-publish_at', '-modified', '-created']

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.body_highlighted = self.highlight_code(self.body)
        super(Post, self).save(self, *args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return('post', (), {
            'slug': self.slug
        })

    def highlight_code(self, body):
        """
        Highlight code in all <pre> elements of body

        BeautifulSoup parses the HTML and extracts all <pre> blocks
        Contents of each <pre> are converted to unicode
        with '<', '>', and '&' unescaped since BeatifulSoup might think
        and '<....>' is a tag and try and close it, etc.

        Then send that unicode through pygments to lex, format, and style it

        The lexer is chosen based on the class of the <pre> (ie 'python', etc)

        Finally replace those <pre> blocks with the new highlighted markup
        and return it as unicode
        """
        soup = BeautifulSoup(body)
        preblocks = soup.findAll('pre')
        for pre in preblocks:
            if hasattr(pre, 'class'):
                try:
                    code = ''.join([unicode(item) for item in pre.contents])
                    code = self.unescape_html(code)
                    lexer = lexers.get_lexer_by_name(pre['class'][0])
                    code_hl = highlight(code, lexer, HtmlFormatter())
                    pre.replaceWith(BeautifulSoup(code_hl))
                except:
                    raise
        return soup

    def unescape_html(self, html):
        return html.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')


class GalleryUpload(models.Model):
    """
    Used to easily create Galleries in admin section

    Provided a .zip file of photos it creates a gallery
    """
    zip_file = models.FileField(upload_to='temp',
                                storage=settings.LOCAL_FILE_STORAGE,
                                help_text="Select a .zip file of images to upload")
    gallery = models.ForeignKey(Gallery, null=True, blank=True,
                            help_text="Select a gallery to add these images to. Leave blank to create new gallery.")
    title = models.CharField(max_length=120,
                             help_text="Can be up to 120 characters.")

    def save(self, *args, **kwargs):
        super(GalleryUpload, self).save(*args, **kwargs)
        self.process_zipfile()
        self.delete()

    def delete(self, *args, **kwargs):
        """
        Deletes the zip file used to create the gallery since it is no longer needed
        """
        os.remove(self.zip_file.path)
        super(GalleryUpload, self).delete(*args, **kwargs)

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
                    except Exception:  # PIL doesn't recognize file as an image, so we skip it
                        raise ValidationError('Image failed to validate: %s'
                                              % filename)
                    # Rewind image pointers back to start of file
                    if hasattr(data, 'seek') and callable(data.seek):
                        data.seek(0)

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
