from .base import *

ADMINS = (
    ('Brian Holdefehr', 'bhold45@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'bhold',
        'USER': 'bhold',
        'PASSWORD': os.environ['DB_PASS'],
        'HOST': '',
        'PORT': '',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'unix:/home/bhold/memcached.sock'
    }
}

# MEDIA_URL = STATIC_URL = 'http://d3ry2ziyu0wa1k.cloudfront.net/'
MEDIA_URL = STATIC_URL = 'http://d2blg18fh6tpw9.cloudfront.net/'

