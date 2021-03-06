from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.views.generic.simple import direct_to_template

from blog_wind.feeds import RecentFeed

admin.autodiscover()

urlpatterns = patterns('',
    # Analytics
    url(r'^googlef1fcfa057d2c8dac.html$', direct_to_template, {'template': 'googlef1fcfa057d2c8dac.html'}),
    # Admin
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    # Resume
    url(r'^resume$', direct_to_template, {'template': 'resume.html'}, name='resume'),
    # Blog
    url(r'^$', 'blog_wind.views.home', name='home'),
    url(r'^page/(?P<page>\d+)$', 'blog_wind.views.home', name='paged_home'),
    url(r'^writing$', 'blog_wind.views.writing', name='writing'),
    url(r'^photos$', 'blog_wind.views.galleries', name='galleries'),
    url(r'^about$', direct_to_template, {'template': 'about.html'}, name='about'),
    url(r'^preview/(?P<slug>[-\w]+)$', 'blog_wind.views.preview', name='preview'),
    url(r'^(?P<slug>[-\w]+)$', 'blog_wind.views.post', name='post'),
    # RSS
    url(r'^feeds/recent$', RecentFeed(), name='feed'),
    #Media
    (r'media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    #Static Media
    (r'static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)
