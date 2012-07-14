from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Blog 
    url(r'^$', 'blog_wind.views.home', name='home'),
    url(r'^page/(?P<page>\d+)$', 'blog_wind.views.home', name='paged_home'),
    url(r'^essays$', 'blog_wind.views.essays', name='essays'),
    url(r'^photos$', 'blog_wind.views.galleries', name='galleries'),
    url(r'^(?P<slug>[-\w]+)$', 'blog_wind.views.post', name='post'),

    # Admin
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
