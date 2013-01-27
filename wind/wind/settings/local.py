from .base import *

DEBUG = TEMPLATE_DEBUG = THUMBNAIL_DEBUG = True

TEMPLATE_STRING_IF_INVALID = "Invalid Expression: %s"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '%s/../db/fish.sql' % PROJECT_ROOT,
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
}
