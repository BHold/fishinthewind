from django.contrib.syndication.views import Feed

from blog_wind.models import Post

class RecentFeed(Feed):
    title = "Fish in the Wind by Brian Holdefehr"
    link = "/feeds/recent"
    description = "Recent posts on Fish in the Wind by Brian Holdefehr"

    def items(self):
        return Post.objects.get_active()[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.body
