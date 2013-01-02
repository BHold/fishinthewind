import os
from django.core.files.storage import FileSystemStorage

PROJECT_ROOT = os.path.dirname(__file__)

DEBUG = False
TEMPLATE_DEBUG = DEBUG

TIME_ZONE = 'America/New_York'

LANGUAGE_CODE = 'en-us'

SITE_ID = 1

USE_I18N = False

USE_L10N = False

USE_TZ = False

MEDIA_ROOT = '%s/../blog_wind/media/' % PROJECT_ROOT

MEDIA_URL = '/media/'

STATIC_ROOT = '%s/static/' % PROJECT_ROOT

STATIC_URL = '/static/'

STATICFILES_DIRS = (
    "%s/../blog_wind/static" % PROJECT_ROOT,
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
    '%s/../blog_wind/templates' % PROJECT_ROOT,
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
    'grappelli',

    'django.contrib.admin', # Grappelli needs to be installed before admin

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
LOCAL_FILE_STORAGE = FileSystemStorage(location='%s/../blog_wind/' % PROJECT_ROOT)

# So can use debug context processor
INTERNAL_IPS = ('127.0.0.1',)

# Settings used by fabfile
LOCAL_PROJECT_ROOT = PROJECT_ROOT + "/../"
REMOTE_PROJECT_ROOT = "/home/bhold/webapps/django/fishinthewind/wind/"
BASE_HTML_FILENAME = "base.html"
LIVE_SETTINGS = PROJECT_ROOT + "/live_settings.py"
REMOTE_LIVE_SETTINGS = REMOTE_PROJECT_ROOT + "wind/live_settings.py"
REMOTE_HOST_DOMAIN = "bhold.webfactional.com"
REMOTE_HOST_USER = "bhold"
RESTART_PATH = "$HOME/webapps/django/apache2/bin/restart"
RUN_TESTS = True
TEST_APPS = ['blog_wind']
APPS_TO_MIGRATE = ['blog_wind']
USING_LESS = True

# Grappelli settings
GRAPPELLI_ADMIN_TITLE = "Brian Holdefehr"


try:
    from local_settings import *
except ImportError:
    try:
        from live_settings import *
    except ImportError:
        pass
