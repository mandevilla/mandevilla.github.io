#!/usr/bin/env python
# -*- mode: python -*- -*- coding: utf-8 -*-
try:
    from ConfigParser import SafeConfigParser as ConfigParser
except:
    from configparser import ConfigParser
import datetime
import io
import os
import sys

##
## settings
##
DEFAULT_ENCODING = 'utf-8'
PY3 = sys.version_info[0] == 3
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
# config
DEFAULT_CONFIG_FILE = 'default.cfg'
SITE_CONFIG_FILE = 'site.cfg'
parser = ConfigParser()
for ini in (DEFAULT_CONFIG_FILE, SITE_CONFIG_FILE):
    fullpath = os.path.join(ROOT_DIR, ini)
    if not os.path.exists(fullpath):
        continue
    if not PY3:
        inifile = io.open(fullpath, encoding=DEFAULT_ENCODING)
        parser.readfp(inifile, fullpath)
    else:
        parser.read(fullpath)

##
## general
##
APP_NAME = parser.get('DEFAULT', 'app_name')
MODE = parser.get('DEFAULT', 'mode')
BASE_URL = parser.get('DEFAULT', 'base_url')

##
## site
##
SITE_CONFIG = dict(parser.items('site'))

##
## directory
##
DATA_DIR = os.path.join(ROOT_DIR, parser.get('directory', 'data'))
LOG_DIR = os.path.join(ROOT_DIR, parser.get('directory', 'log'))
DEPLOY_DIR = os.path.join(ROOT_DIR, parser.get('directory', 'deploy'))
TEMPLATE_DIR = os.path.join(ROOT_DIR, parser.get('directory', 'templates'))
SNIPPET_DIR = os.path.join(ROOT_DIR, parser.get('directory', 'snippets'))
MEDIA_DIR = os.path.join(ROOT_DIR, parser.get('directory', 'media'))
IMAGE_DIR = os.path.join(ROOT_DIR, parser.get('directory', 'image'))
FACEBOOK_IMAGE_DIR = os.path.join(ROOT_DIR,
                                  parser.get('directory', 'facebook_image'))

##
## data
##
EXCEPT_TEMPLATES = [x.strip() for x in
                    parser.get('data', 'except_templates').split(',')]
PHOTO_THUMBNAIL_SIZE = parser.getint('data', 'photo_thumbnail_size')
THUMBNAIL_CROP_SIZE = parser.getint('data', 'thumbnail_crop_size')
THUMBNAIL_PREFIX = parser.get('data', 'thumbnail_prefix')
FACEBOOK_TIMESTAMP = parser.get('data', 'facebook_timestamp')
FACEBOOK_LIMIT = parser.getint('data', 'facebook_limit')
FACEBOOK_TRUNCATE_URL_LENGTH = parser.getint(
    'data', 'facebook_truncate_url_length')
FACEBOOK_TRUNCATE_MESSAGE_LENGTH = parser.getint(
    'data', 'facebook_truncate_message_length')
MEDIA_URL = parser.get('data', 'media_url')
WEEK_MAP = (u'月', u'火', u'水', u'木', u'金', u'土', u'日')
# banner
BANNER_X_POSITION = 308
BANNER_Y_POSITION = 32
BANNER_COLOR = '#ffffff'
BANNER_FONT = 'Vera.ttf'
BANNER_FONT_SIZE = 20

##
## log
##
DEBUG_LOG = os.path.join(LOG_DIR, parser.get('log', 'debug_log'))
error_log = parser.get('log', 'error_log')
if error_log:
    ERROR_LOG = os.path.join(LOG_DIR, error_log)
else:
    ERROR_LOG = ''

##
## sns
##
SNS_MEDIA_BOX_SHOW = parser.getboolean('sns', 'media_box_show')
SNS_MEDIA_BOX_TYPE = parser.get('sns', 'media_box_type')
USE_OGP = parser.getboolean('sns', 'use_ogp')

##
## mail
##
MAIL_CONFIG = dict(parser.items('mail'))
GMAIL_CONFIG = dict(parser.items('gmail'))

##
## facebook
##
FACEBOOK_CONFIG = dict(parser.items('facebook'))
FACEBOOK_MANDEVILLA_CONFIG = dict(parser.items('facebook_mandevilla'))
FACEBOOK_FULL_FIELDS = ('id', 'from', 'to', 'message', 'picture',
                        'full_picture', 'attachments', 'link', 'name',
                        'caption', 'description', 'source', 'properties',
                        'icon', 'type', 'likes', 'comments', 'object_id',
                        'application','created_time', 'updated_time',
                        'targeting')
FACEBOOK_FIELDS = ('id', 'object_id', 'message', 'privacy', 'attachments',
                   'link', 'likes', 'comments', 'created_time', 'updated_time')
