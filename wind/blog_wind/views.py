from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.http import Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext

from blog_wind.models import Post


def home(request, page=1):
    """
    Home page for blog

    Will display most recents posts regardless of
    if they are essays or galleries
    """

    all_posts = Post.objects.get_posted()

    paginator = Paginator(all_posts, 5)

    # if page number out of range, give last page
    try:
        posts = paginator.page(page)
    except (EmptyPage, InvalidPage):
        posts = paginator.page(paginator.num_pages)

    variables = RequestContext(request, {
        'posts': posts
    })
    return render_to_response('home.html', variables)


def post(request, slug):
    """
    Displays an individual post

    Post must be active and published date must be in the past
    """

    try:
        post = Post.objects.get_posted().get(slug=slug)
    except Post.DoesNotExist:
        raise Http404

    variables = RequestContext(request, {
        'post': post
    })
    return render_to_response('post.html', variables)


def preview(request, slug):
    """
    Displays an individual post in preview mode

    Post does not need to be active and publish date can be in future
    """

    post = get_object_or_404(Post, slug=slug)

    variables = RequestContext(request, {
        'post': post
    })
    return render_to_response('preview.html', variables)


def writing(request):
    """
    A page that will list all of the posts that are writing only
    """

    writings = Post.objects.get_posted().filter(gallery__isnull=True)

    variables = RequestContext(request, {
        'writings': writings
    })
    return render_to_response('writing.html', variables)


def galleries(request):
    """
    A page that will list all of the posts that are galleries only
    """

    galleries = Post.objects.get_posted().filter(gallery__isnull=False)

    variables = RequestContext(request, {
        'galleries': galleries
    })
    return render_to_response('galleries.html', variables)
