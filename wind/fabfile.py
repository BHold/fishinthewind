from __future__ import with_statement
import os

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

os.environ["DJANGO_SETTINGS_MODULE"] = "wind.settings"

from boto.exception import S3ResponseError
from boto.s3.connection import S3Connection
from bs4 import BeautifulSoup
from cssmin import cssmin
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from fabric.api import local, run, env, cd, lcd, put, task
from fabric.contrib.console import confirm
from hashlib import md5
from slimit import minify

REMOTE_PROJECT_ROOT = getattr(settings, "REMOTE_PROJECT_ROOT", None)
LOCAL_PROJECT_ROOT = getattr(settings, "LOCAL_PROJECT_ROOT", None)
STATIC_DIRS = getattr(settings, "STATICFILES_DIRS", ())
TEMPLATE_DIRS = getattr(settings, "TEMPLATE_DIRS", ())
BASE_HTML_FILENAME = getattr(settings, "BASE_HTML_FILENAME", "")
ACCESS_KEY = getattr(settings, "AWS_ACCESS_KEY_ID", None)
SECRET_ACCESS_KEY = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
BUCKET_NAME = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
HEADERS = getattr(settings, "AWS_HEADERS", None)
AUTO_CREATE_BUCKET = getattr(settings, "AWS_AUTO_CREATE_BUCKET", False)
SHOULD_GZIP = getattr(settings, "AWS_IS_GZIPPED", True)
BUCKET_ACL = getattr(settings, "BUCKET_ACL", "public-read")
DEFAULT_ACL = getattr(settings, "DEFAULT_ACL", "public-read")
LIVE_SETTINGS = getattr(settings, "LIVE_SETTINGS", None)
REMOTE_LIVE_SETTINGS = getattr(settings, "REMOTE_LIVE_SETTINGS", None)
REMOTE_HOST_DOMAIN = getattr(settings, "REMOTE_HOST_DOMAIN", None)
REMOTE_HOST_USER = getattr(settings, "REMOTE_HOST_USER", None)
RUN_TESTS = getattr(settings, "RUN_TESTS", False)
TEST_APPS = getattr(settings, "TEST_APPS", ())
RESTART_PATH = getattr(settings, "RESTART_PATH", None)
APPS_TO_MIGRATE = getattr(settings, "APPS_TO_MIGRATE", ())

if SHOULD_GZIP:
    from gzip import GzipFile

if not REMOTE_HOST_DOMAIN or not REMOTE_HOST_USER:
    raise ImproperlyConfigured("You must specify REMOTE_HOST_DOMAIN and "
        "REMOTE_HOST_USER variables in your settings.py")

env.hosts = ["{0}@{1}".format(REMOTE_HOST_USER, REMOTE_HOST_DOMAIN)]


def _compress_content(content):
    """
    Gzip a given string.
    """
    buf = StringIO()
    with GzipFile(fileobj=buf, mode="wb") as gzf:
        gzf.write(content)
    return buf.getvalue()


def _s3_upload(filename, content, content_type):
    """
    Upload a file to S3 given a name and content
    """
    conn = S3Connection(ACCESS_KEY, SECRET_ACCESS_KEY)

    try:
        bucket = conn.get_bucket(BUCKET_NAME, validate=AUTO_CREATE_BUCKET)
    except S3ResponseError:
        if AUTO_CREATE_BUCKET:
            bucket = conn.create_bucket(BUCKET_NAME)
            bucket.set_acl(BUCKET_ACL)
        else:
            raise ImproperlyConfigured("Bucket given by AWS_STORAGE_BUCKET "
                "doesn't exist. Buckets can be created automatically by "
                "setting AWS_AUTO_CREATE_BUCKET to True")

    k = bucket.get_key(filename)
    if not k:
        k = bucket.new_key(filename)
    k.set_metadata("Content-Type", content_type)

    if SHOULD_GZIP:
        content = _compress_content(content)
        HEADERS.update({"Content-Encoding": "gzip"})

    k.set_contents_from_string(content,
                               headers=HEADERS, policy=DEFAULT_ACL)


def _find_file(filename, directories):
    """
    Tries to find a filename within an iterable of given directories
    """
    for directory in directories:
        if not directory.endswith("/") and not filename.startswith("/"):
            directory += "/"
        file_path = directory + filename
        if os.path.isfile(file_path):
            return file_path
    return None


def _get_base_html():
    """
    Tries to find base HTML file.

    Raises ImproperlyConfigured if it fails to find it
    """
    html = _find_file(BASE_HTML_FILENAME, TEMPLATE_DIRS)
    if html:
        return html
    raise ImproperlyConfigured("Can't find BASE_HTML_FILE: '{0}'. Make sure "
                        "it can be accessed from one of your TEMPLATE_DIRS"
                        .format(BASE_HTML_FILENAME))


def _get_static_file(filepath):
    if "{{ STATIC_URL }}" in filepath:
        filepath = filepath.replace("{{ STATIC_URL }}", "")
    static_file = _find_file(filepath, STATIC_DIRS)
    if static_file:
        return static_file
    raise ImproperlyConfigured("Can't find static file: '{0}'. Make sure "
                        "it can be accessed from one of your STATIC_DIRS"
                        .format(filepath))


def _update_static(exts):
    """
    Implements the combination, minification, and compression of static files.

    Filename is hashed so a far future Expires header can be set on it.
    Thus, we need to change the filename (the hash) when we make changes.
    """
    base_html_file = _get_base_html()
    with open(base_html_file, "r") as base:
        # BeautifulSoup is used to find js/css links in HTML to be combined
        # and to replace old links with ones to the soon to be compressed files
        #
        # We use python's builtin 'html.parser' because lxml was causing issues
        # with Django template tags for me. It was moving my {% if %} tag out
        # of <head> and adding <p> tags around it for some reason
        soup = BeautifulSoup(base.read(), "html.parser")

    # For both js and css if updating both
    for ext in exts:
        files_to_include = soup.select(".minify-{0}".format(ext))
        if not files_to_include:
            continue

        combined = ""
        for static_file in files_to_include:
            if ext == "css":
                fname = _get_static_file(static_file["href"])
            else:
                fname = _get_static_file(static_file["src"])
            with open(fname, "r") as f:
                combined += f.read()

        hashed_name = "{0}/{1}.min.{0}".format(ext, md5(combined).hexdigest())

        if ext == "css":
            minifier = cssmin
            content_type = "text/css"
        else:
            minifier = minify
            content_type = "application/javascript"

        minified = minifier(combined)
        _s3_upload(hashed_name, minified, content_type)

        destination = soup.select(".minified-{0}".format(ext))[0]
        if not destination:
            raise ImproperlyConfigured("You need a {0} element with a class "
                "of 'minified-{1}' as a placeholder element for the compressed"
                " {2} {0}.".format("link" if ext == "css" else "script",
                                   ext, ext.upper()))

        if "{{ STATIC_URL }}" in destination.attrs["href"]:
            new_href = "{{ STATIC_URL }}" + hashed_name
        else:
            new_href = hashed_name

        destination.attrs["href"] = new_href

    # Write changed href(s) to base HTML file
    with open(base_html_file, "w") as f:
        f.write(unicode(soup.prettify()))


@task
def syncdb():
    """
    Syncs the database on server
    """
    with cd(REMOTE_PROJECT_ROOT):
        run("./manage.py syncdb")


@task
def migrate_database():
    """
    Migrates the database on server
    """
    if not APPS_TO_MIGRATE:
        raise ImproperlyConfigured("Setting APPS_TO_MIGRATE must be set in "
                                   "order to migrate")
    with cd(REMOTE_PROJECT_ROOT):
        for app in APPS_TO_MIGRATE:
            run("./manage.py schemamigration {0} --auto".format(app))
            run("./manage.py migrate {0}".format(app))


@task
def update_css():
    """
    Combines, minifies, and compresses CSS stylesheets.
    """
    _update_static(("css",))


@task
def update_js():
    """
    Combines, minifies, and compresses JS scripts.
    """
    _update_static(("js",))


@task
def update_css_and_js():
    """
    Combines, minifies, and compresses CSS stylesheets and JS scripts.
    """
    _update_static(("css", "js"))


@task
def transfer_settings():
    """
    Transfers live_settings.py to the server
    """
    if not LIVE_SETTINGS or not REMOTE_LIVE_SETTINGS \
            or not os.path.isfile(LIVE_SETTINGS):
        raise ImproperlyConfigured("Please make sure LIVE_SETTINGS and "
            "REMOTE_LIVE_SETTINGS are set properly in your settings.py")
    put(LIVE_SETTINGS, REMOTE_LIVE_SETTINGS)


@task
def restart():
    """
    Restarts server
    """
    if not RESTART_PATH:
        raise ImproperlyConfigured("Settings variable RESTART_PATH must be set"
            " to the remote path of the server's restart script")
    run("source {0}".format(RESTART_PATH))


@task
def run_tests():
    """
    Runs tests for the project

    Defaults to running tests for all installed apps, but will only run tests
    for the apps listed in TEST_APPS if assigned
    """
    if RUN_TESTS:
        test_apps = ' '.join(TEST_APPS)
        with lcd(LOCAL_PROJECT_ROOT):
            local("./manage.py test {0}".format(test_apps))


@task
def deploy():
    """
    Deploys the blog to the server.

    Asks user if we need to update css, syncdb, or migrate and responds
    accordingly.

    Finally restarts server
    """
    new_css = new_js = sync = migrate = False
    if confirm("Do we need to update css or js, syncdb, or migrate?",
               default=False):
        new_css = confirm("Update CSS?")
        new_js = confirm("Update JS?")
        sync = confirm("Sync database?")
        migrate = confirm("Migrate?")

    if new_css or new_js:
        if new_css and new_js:
            update_css_and_js()
        if new_css:
            update_css()
        if new_js:
            update_js()
        with lcd(LOCAL_PROJECT_ROOT):
            local("git commit -a -m 'New static links in base HTML.'")

    run_tests()

    with lcd(LOCAL_PROJECT_ROOT):
        local("git push")

    with cd(REMOTE_PROJECT_ROOT):
        run("git pull")

    if sync:
        syncdb()
    if migrate:
        migrate_database()

    restart()
