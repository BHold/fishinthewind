from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.simple import direct_to_template

from blog_wind.feeds import RecentFeed

admin.autodiscover()

urlpatterns = patterns('',
    # Admin
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    # Blog 
    url(r'^$', 'blog_wind.views.home', name='home'),
    url(r'^page/(?P<page>\d+)$', 'blog_wind.views.home', name='paged_home'),
    url(r'^writing$', 'blog_wind.views.writing', name='writing'),
    url(r'^photos$', 'blog_wind.views.galleries', name='galleries'),
    url(r'^about$', direct_to_template, {'template': 'about.html'}, name='about'), 
    url(r'^post/(?P<slug>[-\w]+)$', 'blog_wind.views.post', name='post'),
    # RSS
    url(r'^feeds/recent$', RecentFeed(), name='feed'),
)
