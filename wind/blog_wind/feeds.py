from django.contrib.syndication.views import Feed

from blog_wind.models import Post


class RecentFeed(Feed):
    title = "Brian Holdefehr's Blog"
    link = "/feeds/recent"
    description = "Recent posts by Brian Holdefehr"

    def items(self):
        return Post.objects.get_active()[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.body
