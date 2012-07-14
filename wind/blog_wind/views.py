from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.core.paginator import Paginator, InvalidPage, EmptyPage

from blog_wind.models import Post

def home(request, page=1):
    """
    Home page for blog

    Will display most recents posts regardless of
    if they are essays or galleries
    """

    all_posts = Post.objects.get_active()

    paginator = Paginator(all_posts, 7)

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
    """

    post = get_object_or_404(Post, slug=slug)

    variables = RequestContext(request, {
        'post': post 
    })
    return render_to_response('post.html', variables)

def essays(request):
    """
    A page that will list all of the posts that are essays only
    """ 

    essays = Post.objects.get_active().filter(is_gallery=False)

    variables = RequestContext(request, {
        'essays': essays
    })
    return render_to_response('essays.html', variables)

def galleries(request):
    """
    A page that will list all of the posts that are galleries only
    """

    galleries = Post.objects.get_active().filter(is_gallery=True)

    variables = RequestContext(request, {
        'galleries': galleries 
    })
    return render_to_response('galleries.html', variables)
