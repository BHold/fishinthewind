from __future__ import with_statement
import gzip
import os

os.environ['DJANGO_SETTINGS_MODULE'] = "wind.settings"

from boto.s3.connection import S3Connection
from cssmin import cssmin
from django.conf import settings
from hashlib import md5
from fabric.api import local, run, env, cd, lcd
from fabric.contrib.console import confirm
from bs4 import BeautifulSoup

REMOTE_PROJECT_ROOT = "/home/bhold/webapps/django/fishinthewind/wind"
LOCAL_PROJECT_ROOT = "/Users/bhold/Sites/blog/wind"
STATIC_ROOT = LOCAL_PROJECT_ROOT + "/blog_wind/static/"
TEMP_ROOT = LOCAL_PROJECT_ROOT + "/blog_wind/temp/"
HTML_BASE_FILE = LOCAL_PROJECT_ROOT + "/blog_wind/templates/base.html"

env.hosts = ['bhold@bhold.webfactional.com']


def syncdb():
    """
    Syncs the database on server if needed
    """
    with cd(REMOTE_PROJECT_ROOT):
        run("./manage.py syncdb")


def migrate_database():
    """
    Migrates the database on server if needed
    """
    with cd(REMOTE_PROJECT_ROOT):
        run("./manage.py schemamigration --auto blog_wing")
        run("./manage.py migrate blog_wind")


def _compress_content(filename, content):
    """Gzip a given string."""
    with gzip.open(filename, 'wb') as f:
        f.write(content)
    return filename


def _s3_upload(filename, content, content_type):
    """
    Upload a file to S3 given a name and content
    """
    conn = S3Connection(settings.AWS_ACCESS_KEY_ID,
                        settings.AWS_SECRET_ACCESS_KEY)

    try:
        bucket = conn.get_bucket(settings.AWS_STORAGE_BUCKET_NAME, validate=True)
    except:
        bucket = conn.create_bucket(settings.AWS_STORAGE_BUCKET_NAME)
        bucket.set_acl('public-read')

    k = bucket.get_key(filename)
    if not k:
        k = bucket.new_key(filename)
    k.set_metadata('Content-Type', content_type)

    headers = settings.AWS_HEADERS

    temp_file = TEMP_ROOT + filename
    temp_file = _compress_content(temp_file, content)
    headers.update({'Content-Encoding': 'gzip'})

    k.set_contents_from_filename(temp_file, headers=headers, policy='public-read')

    # No longer need the temp file
    os.remove(temp_file)


def update_css():
    """
    Creates an md5 hash of stylesheets, minifies them, and uploads to s3

    File hashed because we set a far future Expires header on all static
    content. Thus, we need to change the filename when we make changes
    """
    with open(HTML_BASE_FILE, 'r') as base:
        soup = BeautifulSoup(base.read())

    css_links = soup.select('.minify-me')
    css_combined = ''
    for link in css_links:
        css_file = link['href'].replace('{{ STATIC_URL }}', STATIC_ROOT)
        with open(css_file, 'r') as f:
            css_combined += f.read()

    css_hash = 'css/' + md5(css_combined).hexdigest() + '.min.css'

    minified = cssmin(css_combined)
    _s3_upload(css_hash, minified, 'text/css')

    new_href = '{{ STATIC_URL }}' + css_hash
    soup.select('.minified')[0].attrs['href'] = new_href

    # Write changed href to base.html
    with open(HTML_BASE_FILE, 'w') as f:
        f.write(unicode(soup))


def deploy():
    """
    Deploys the blog to the server.

    Asks user if we need to update css, syncdb, or migrate and responds
    accordingly.
    """
    if confirm("Do we need to update css, syndb, or migrate?", default=False):
        new_css = confirm("Update CSS?")
        sync = confirm("Sync database?")
        migrate = confirm("Migrate?")

    if new_css:
        update_css()
        with lcd(LOCAL_PROJECT_ROOT):
            local("git commit -a -m \"Updated css link in base.html\"")

    with lcd(LOCAL_PROJECT_ROOT):
        local("git push")

    with cd(REMOTE_PROJECT_ROOT):
        run("git pull")

    if sync:
        syncdb()
    if migrate:
        migrate_database()

    run("source $HOME/webapps/django/apache2/bin/restart")


def transfer_settings():
    local("scp /Users/bhold/Sites/blog/wind/wind/live_settings.py bhold@bhold.webfactional.com:/home/bhold/webapps/django/fishinthewind/wind/wind/live_settings.py")
