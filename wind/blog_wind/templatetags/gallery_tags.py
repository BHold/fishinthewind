from django import template
from django.db.models import F

register = template.Library()

@register.filter
def random_image(photos):
    """
    Chooses a random photo from the gallery to display

    Makes sure the photo is of landscape orientation
    """
    random_photo = photos.filter(width__gt=F('height')).order_by('?')[0]
    return random_photo
