import datetime
import os

from django.core.files.storage import FileSystemStorage

PROJECT_ROOT = os.path.dirname(__file__) + "/../../"

DEBUG = False
TEMPLATE_DEBUG = DEBUG

TIME_ZONE = 'America/New_York'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = False

USE_L10N = False

USE_TZ = False

MEDIA_ROOT = '%s/media/' % PROJECT_ROOT

MEDIA_URL = '/media/'

STATIC_ROOT = '%s/wind/static' % PROJECT_ROOT

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    '%s/static' % PROJECT_ROOT,
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'wind.urls'

WSGI_APPLICATION = 'wind.wsgi.application'

TEMPLATE_DIRS = (
    '%s/templates' % PROJECT_ROOT,
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admindocs',

    'south',
    'storages',
    'sorl.thumbnail',
    # 'grappelli',

    'django.contrib.admin',  # Grappelli needs to be installed before admin

    'blog_wind'
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Used to store gallery .zipfiles locally, instead of at MEDIA_ROOT since there
# is no need to send them to S3
LOCAL_FILE_STORAGE = FileSystemStorage(location=PROJECT_ROOT)

# So can use debug context processor
INTERNAL_IPS = ('127.0.0.1',)

# Settings used by fabfile
LOCAL_PROJECT_ROOT = PROJECT_ROOT
REMOTE_PROJECT_ROOT = "$HOME/webapps/django/fishinthewind/wind/"
BASE_HTML_FILENAME = "base.html"
REMOTE_HOST_DOMAIN = "web349.webfaction.com"
REMOTE_HOST_USER = "bhold"
RESTART_PATH = "$HOME/webapps/django/apache2/bin/restart"
RUN_TESTS = True
TEST_APPS = ['blog_wind']
APPS_TO_MIGRATE = ['blog_wind']
REQUIREMENTS_FILE_PATH = "../requirements.txt"

# Grappelli settings
GRAPPELLI_ADMIN_TITLE = "Brian Holdefehr"

CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = (60 * 60)
CACHE_MIDDLEWARE_PREFIX = ''

SECRET_KEY = os.environ['FISH_SECRET_KEY']

# AWS_ACCESS_KEY_ID = 'AKIAIL6DJPWZAVLJAAHQ'
AWS_ACCESS_KEY_ID = 'AKIAIHAD2NWPPG7JXAUA'
AWS_SECRET_ACCESS_KEY = os.environ['FISH_AWS_SECRET_KEY']
AWS_STORAGE_BUCKET_NAME = 'fishinthewind2'
AWS_AUTO_CREATE_BUCKET = True
AWS_IS_GZIPPED = True

future = datetime.datetime.now() + datetime.timedelta(days=364)
AWS_HEADERS = {
    'Expires': future.strftime('%a, %d %b %Y %H:%M:%S GMT'),
    'Cache-Control': 'max-age=31536000, public'
}

# Uploaded media, and static files via collectstatic both use this backend to
# send files to s3
DEFAULT_FILE_STORAGE = STATICFILES_STORAGE = 'wind.storage.StaticToS3Storage'
