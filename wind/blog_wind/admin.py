from django.contrib import admin

from blog_wind.models import Post

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
            'fields': ('active', 'publish_at', 'is_gallery'),
        }),
        ('Contents', {
            'fields': ('body',),
        }),
        ('Optional', {
            'fields': ('slug',),
            'classes': ('collapse',),
        })
    )

admin.site.register(Post, PostAdmin)
