import datetime

from django.db import models

class PostManager(models.Manager):
    """
    Manager for Posts which provides a function to filter for posts which should be active
    """
    def get_active(self):
        return self.get_query_set().filter(publish_at__lte=datetime.datetime.now(), active=True)

class Post(models.Model):
    title = models.CharField(max_length=150,
                             help_text="Title of post, can be up to 150 characters.")
    slug = models.SlugField()
    body = models.TextField(help_text="Main body text for post. Can use html tags. Paragraph tags will be used automatically before/after open line")
    active = models.BooleanField(default=True,
                                 help_text="Controls whether or not post is live to the world.")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    publish_at = models.DateTimeField(default=datetime.datetime.now(),
                                      help_text="Date and time post should become active.")
    is_gallery = models.BooleanField(default=False)

    objects = PostManager()

    def __unicode__(self):
        return self.title
        

    @models.permalink
    def get_absolute_url(self):
        return('blog_post', (), {
            'slug': self.slug
        })

    class Meta:
        ordering = ['-publish_at', '-modified', '-created']
