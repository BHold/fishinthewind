from django.contrib import admin
from sorl.thumbnail.admin import AdminImageMixin

from blog_wind.models import Post, Photo, Gallery, GalleryUpload

class PostAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('title',)}
    list_display = ('active', 'title', 'publish_at')
    list_display_links = ('title',)
    list_editable = ('active',)
    list_filter = ('publish_at', 'modified', 'created', 'active')
    date_hierarchy = 'publish_at'
    search_fields = ['title', 'body']
    fieldsets = (
        (None, {
            'fields': ('title',),
        }),
        ('Publication', {
            'fields': ('active', 'publish_at'),
        }),
        ('Contents', {
            'fields': ('body', 'gallery'),
        }),
        ('Optional', {
            'fields': ('slug',),
            'classes': ('collapse',),
        })
    )

admin.site.register(Post, PostAdmin)

class GalleryAdmin(admin.ModelAdmin):
    list_display = ('active', 'title', 'created')
    list_display_links = ('title',)
    list_editable = ('active',)
    list_filter = ('created', 'modified', 'active')
    date_hierarchy = 'created'
    search_fields = ['title']

admin.site.register(Gallery, GalleryAdmin)

class GalleryUploadAdmin(admin.ModelAdmin):
    pass

admin.site.register(GalleryUpload, GalleryUploadAdmin)

class PhotoAdmin(AdminImageMixin, admin.ModelAdmin):
    list_display = ('active', 'title', 'image')
    list_display_links = ('title',)
    list_editable = ('active',)
    list_filter = ('created', 'modified', 'active')
    date_hierarchy = 'created'
    search_fields = ['title']

admin.site.register(Photo, PhotoAdmin)

