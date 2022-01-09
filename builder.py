#!/usr/bin/env python
# -*- mode: python -*- -*- coding: utf-8 -*-
import json
import datetime
import logging
from logging.handlers import (RotatingFileHandler, SMTPHandler)
import optparse
import os
import re
import sys
import time

from jinja2 import Environment, FileSystemLoader

from lib.image import (make_thumb_via_url, make_thumb, open_image, insert_text)
from lib.webapi import (FaceBook, FBMandevilla)
from config import (PY3, APP_NAME, DEFAULT_ENCODING, MODE, DATA_DIR, LOG_DIR,
                    FACEBOOK_TIMESTAMP, FACEBOOK_IMAGE_DIR,
                    FACEBOOK_MANDEVILLA_CONFIG, FACEBOOK_TRUNCATE_URL_LENGTH,
                    FACEBOOK_TRUNCATE_MESSAGE_LENGTH, THUMBNAIL_PREFIX,
                    THUMBNAIL_CROP_SIZE, PHOTO_THUMBNAIL_SIZE, MAIL_CONFIG,
                    DEBUG_LOG, ERROR_LOG, WEEK_MAP, BASE_URL, MEDIA_URL,
                    MEDIA_DIR, TEMPLATE_DIR, DEPLOY_DIR, SNIPPET_DIR,
                    EXCEPT_TEMPLATES, USE_OGP, SNS_MEDIA_BOX_SHOW,
                    SNS_MEDIA_BOX_TYPE, SITE_CONFIG, IMAGE_DIR, GMAIL_CONFIG)

if PY3:
    from urllib.request import (urlopen, HTTPError, URLError)
else:
    from urllib2 import (urlopen, HTTPError, URLError)
    reload(sys)
    sys.setdefaultencoding(DEFAULT_ENCODING)

###
### functions
###
def parse_json(url):
    try:
        return json.loads(urlopen(url).read())
    except HTTPError as e:
        print (e), ('parse_json'),  (url)
        raise Exception

def convert_date_ja(d, with_time=False, with_week=False):
    t = d.strftime(u'%Y年x%m月x%d日')
    if with_week:
        t += u'(%s)' % WEEK_MAP[d.weekday()]
    if with_time:
        t += d.strftime(u'x%H時x%M分')
    return t.replace('x0', '').replace('x', '').replace(u'時0分', u'時')

def str2date(s):
    s, d = s.split('+')
    s = time.strptime(s, '%Y-%m-%dT%H:%M:%S')[:6]
    result = datetime.datetime(*s)
    if d == '0000':
        result += datetime.timedelta(hours=9)
    return result

##
## classes
##
class Logger(object):
    def __init__(self):
        # logging
        self.set_logger()

    def set_logger(self, app_name=APP_NAME, log_dir=LOG_DIR,
                   debug_log=DEBUG_LOG, error_log=ERROR_LOG,
                   max_byte=100000, backup_count=10):
        self.logger = logging.getLogger(app_name)
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        )
        #formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        ## debug log
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        debug_handler = RotatingFileHandler(debug_log, maxBytes=max_byte,
                                            backupCount=backup_count)
        debug_handler.setFormatter(formatter)
        self.logger.addHandler(debug_handler)

        ## error log
        if error_log:
            error_handler = RotatingFileHandler(error_log, maxBytes=max_byte,
                                                backupCount=backup_count)
        else:
            error_handler = SMTPHandler(mailhost=GMAIL_CONFIG['host'],
                                        fromaddr=GMAIL_CONFIG['sender'],
                                        toaddrs=MAIL_CONFIG['recipients'],
                                        subject='%s Failed' % app_name,
                                        credentials=(
                                            GMAIL_CONFIG['user'],
                                            GMAIL_CONFIG['password']))
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)

        # set default level
        self.logger.setLevel(logging.DEBUG)

class Fetch(Logger):
    def __init__(self, timestamp_key=FACEBOOK_TIMESTAMP):
        self.now = datetime.datetime.now()
        self.today = self.now.date()
        self.timestamp_key = timestamp_key
        Logger.__init__(self)
        self.facebook = FBMandevilla()

    def get_facebook(self, image_dir=FACEBOOK_IMAGE_DIR,
                     prefix=THUMBNAIL_PREFIX, size=PHOTO_THUMBNAIL_SIZE,
                     crop=THUMBNAIL_CROP_SIZE, override=False,
                     deploy_dir=DEPLOY_DIR, media_dir=MEDIA_DIR,
                     media_url=MEDIA_URL):

        data = self.facebook.get_feed()
        feed_data = facebook_page.parse_feed(data)

        result = []
        for x in feed_data:
            y = dict()
            y['object_id'] = x.get('object_id')
            message = x.get('message')
            if not message:
                messge = u''
            y[self.timestamp_key] = str2date(x.get(self.timestamp_key))
            if x.get('pictures'):
                image_url = x['pictures'][0]['src']
                s = image_url.split('/')
                filename = s[-1]
                pos = filename.find('?')
                if pos != -1:
                    filename = filename[:pos]
                f, e = os.path.splitext(filename)
                if e not in ('.jpg', '.JPG', '.jpeg', '.JPEG'):
                    continue
                picture = os.path.join(image_dir, filename)
                thumbnail = os.path.join(image_dir, prefix + filename)
                if override or (not (os.path.exists(picture)
                                     or os.path.exists(thumbnail))):
                    _picture = make_thumb_via_url(url=image_url,
                                                  filename=picture,
                                                  size=size, crop=False)
                    _thumb = make_thumb_via_url(url=image_url,
                                                filename=thumbnail,
                                                size=crop, crop=True)
                    if _picture:
                        y['picture'] = picture.replace(media_dir, media_url)
                        self.logger.info('save %s' % y['picture'])
                    if _thumb:
                        y['thumbnail'] = thumbnail.replace(media_dir, '')
                        self.logger.info('save %s' % y['thumbnail'])
                else:
                    y['picture'] = picture.replace(media_dir, media_url)
                    y['thumbnail'] = thumbnail.replace(media_dir, '')

            # if only no-photo post, continue
            if (not override) and not x.get('pictures'):
                continue

            if not y.get('picture'):
                y['picture'] = os.path.join(FACEBOOK_IMAGE_DIR, 'facebook.png')
            if not y.get('thumbnail'):
                y['thumbnail'] = os.path.join(FACEBOOK_IMAGE_DIR,
                                              'tn_facebook.png')

            _likes = x.get('likes')
            if _likes:
                y['likes'] = len(_likes['data'])
            else:
                y['likes'] = 0

            result.append(y)

        if result:
            try:
                result.sort(cmp=lambda x,y: cmp(x[self.timestamp_key],
                                                y[self.timestamp_key]),
                            reverse=True)
            except:
                from functools import cmp_to_key
                def compare_date(x, y):
                    if x[self.timestamp_key] < y[self.timestamp_key]:
                        return -1
                    elif x[self.timestamp_key] > y[self.timestamp_key]:
                        return 1
                    return 0
                result = sorted(result, key=cmp_to_key(compare_date))

        return result

    def set_facebook(self, data, output_dir=SNIPPET_DIR,
                     encoding=DEFAULT_ENCODING, media_url=MEDIA_URL,
                     config=FACEBOOK_MANDEVILLA_CONFIG, limit=10,
                     truncate_url_length=FACEBOOK_TRUNCATE_URL_LENGTH,
                     truncate_message_length=FACEBOOK_TRUNCATE_MESSAGE_LENGTH):

        def truncate_url(url, length=truncate_url_length):
            if len(url) > length:
                title = url[:length] + '...'
            else:
                title = url
            return r'<a href="%s">%s</a>' % (url, title)

        pattern = r'^(https?://\S+)'
        rc = re.compile(pattern , re.DOTALL|re.MULTILINE)

        link_format = 'http://www.facebook.com/%s/posts/%s'
        html_map = {
            'page': {'text': '', 'html': 'facebook_page.html'},
            'summary': {'text': '', 'html': 'facebook_summary.html'}
            }

        i = 0
        data_map = dict()

        for x in data:
            if i >= limit:
                break
            message_list = [y for y in ((x['message'].replace(u'　', ' '))\
                                        .strip()).split('\n') if y]
            summary = '\n'.join(message_list[:1])
            summary = re.sub(rc, lambda m: truncate_url(m.group()),
                             summary)
            summary = summary.replace('\n', '<br />\n')
            if not PY3:
                summary = summary.encode(encoding)
            data_map['summary'] = summary
            data_map['link'] = link_format % (config['username'],
                                              x['object_id'])
            data_map['timestamp'] = convert_date_ja(x[self.timestamp_key],
                                                    with_time=True,
                                                    with_week=True)
            for k in ('picture', 'thumbnail', 'likes', 'message'):
                data_map[k] = x[k]

            # do not show likes, because more than 25 likes not shown
            if data_map['likes']:
                likes_text = '&nbsp;&nbsp;<small class="likes"><img src="%simg/icons/icon_likes.jpg" alt=""/>&nbsp;%s</small>' % (media_url, data_map['likes'])
            else:
                likes_text = ''
            data_map['likes_text'] = likes_text
            html_map['page']['text'] += u'''\
         <div class="row">
           <div class="col-lg-12">
             <h4><a href="%(link)s">%(timestamp)sの投稿%(likes_text)s</a></h4>
           </div>
         </div><!-- row -->
         <div class="row">
           <div class="col-lg-4 photoframe">
               <a href="%(link)s"><img class="img-responsive photoframe" src="%(picture)s" alt="" /></a>
           </div>
           <div class="col-lg-8">
             <p>%(message)s</p>
             <p><a href="%(link)s">Facebookを見る</a></p>
           </div>
         </div><!-- row -->
''' % data_map

            html_map['summary']['text'] += u'''\
          <div class="row">
            <div class="col-lg-12">
              <h4><a href="%(link)s">%(timestamp)sの投稿%(likes_text)s</a></h4>
            </div>
          </div><!-- row -->
          <div class="row">
            <div class="col-lg-4 photoframe">
              <a href="%(link)s"><img class="img-responsive photoframe" src="%(thumbnail)s" alt="" /></a>
            </div>
            <div class="col-lg-8">
              <p>%(summary)s</p>
              <p><a href="%(link)s">Facebookを見る</a></p>
            </div>
          </div><!-- row -->
''' % data_map

            i += 1

        for k, v in html_map.items():
            output = v['text']
            if output:
                output = output.encode(encoding)
                filepath = os.path.join(output_dir, v['html'])
                fp = open(filepath, 'wb')
                fp.write(output)
                fp.close()

    def create_banner(self, likes=0, image_dir=IMAGE_DIR,
                      input_image='banner_facebook.png',
                      output_image='facebook.jpg'):
        if not likes:
            likes = self.get_likes()
        if not likes:
            return

        original_image = os.path.join(image_dir, input_image)
        save_image = os.path.join(image_dir, output_image)
        insert_text(original_image, save_image, '%s' % likes)

    def get_likes(self):
        facebook = FaceBook()
        return facebook.get_profile(self.facebook.object_id).get('likes')

class Builder(Logger):
    def __init__(self, mode=None,
                 output_dir=DEPLOY_DIR, template_dir=TEMPLATE_DIR):
        if mode is None:
            self.mode = MODE
        else:
            self.mode = mode
        self.template_dir = template_dir
        self.output_dir = output_dir

        self.env = Environment(loader=FileSystemLoader(template_dir))
        # logging
        Logger.__init__(self)

    def build_base(self, encoding, base_url, media_url, site, facebook,
                   sns_box_show, sns_box_type):
        now = datetime.datetime.now()
        params = {
            'charset': encoding,
            'site': site,
            'now': now.strftime('%Y/%m/%d'), 'year': now.year,
            'media_url': media_url,
            'base_url': base_url,
            'facebook': facebook,
            'sns': {'box_show': sns_box_show, 'box_type': sns_box_type},
            }
        return params

    def build(self, encoding=DEFAULT_ENCODING, base_url=BASE_URL,
              media_url=MEDIA_URL, except_templates=EXCEPT_TEMPLATES,
              site=SITE_CONFIG, facebook=FACEBOOK_MANDEVILLA_CONFIG,
              use_ogp=USE_OGP, sns_box_show=SNS_MEDIA_BOX_SHOW,
              sns_box_type=SNS_MEDIA_BOX_TYPE):

        base_params = self.build_base(encoding, base_url, media_url, site,
                                      facebook, sns_box_show, sns_box_type)
        html_list = []
        params = base_params.copy()

        for path, dirs, files in os.walk(self.template_dir):
            # eliminate except dir
            if os.path.basename(path) in (x for x in except_templates
                                          if not x.endswith('.html')):
                continue
            for name in files:
                # eliminate except file
                if name in except_templates:
                    continue
                if not name.endswith('.html'):
                    continue
                html = os.path.join(path, name)
                html = html.replace(self.template_dir+'/', '')
                template = self.env.get_template(html)
                extra_param = dict()
                if html == 'index.html':
                    extra_param = {'page': {'title': u'ホーム'},
                                   'use_ogp': True}
                else:
                    extra_param = {'page': dict()}
                params.update(extra_param)
                params.update({'use_ogp': use_ogp})
                data = template.render(**params)
                if not PY3:
                    data = data.decode(encoding)
                output = os.path.join(self.output_dir, html)
                dirname = os.path.dirname(output)
                if not os.path.exists(dirname):
                    os.makedirs(dirname)
                fp = open(output, 'w')
                fp.write(data)
                fp.close()

##
## main
##
def check_args():
    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser()
    parser.add_option(
        '-m', '--mode',
        type='choice',
        choices=['development', 'production'],
        default=None,)
    parser.add_option(
        '-t', '--template-dir',
        dest='template_dir',)
    parser.add_option(
        '-o', '--output-dir',
        dest='output_dir',)
    parser.add_option(
        '-l', '--locale-dir',
        dest='locale_dir',)
    parser.add_option(
        '-r', '--override',
        action='store_true',
        default=False,
        dest='override',
        help='override snippets')
    parser.add_option(
        '-f', '--fetch',
        action='store_true',
        default=False,
        help='fetch data from other service')

    (options, args) = parser.parse_args()
    template_dir = options.template_dir
    return (options, args)

def main():
    # check args
    options, args = check_args()

    # mode
    mode = options.mode
    if not mode:
        mode = MODE

    # create instance
    L = Logger()
    F = Fetch()
    B = Builder(mode=mode)

    try:
        """
        # fetch
        if options.fetch:
            # fetch facebook data
            if mode == 'development':
                from lib.mock import data
            else:
                data = F.get_facebook(override=options.override)
            if data:
                F.set_facebook(data=data)
                F.create_banner()
        """
        # build
        B.build()
    except URLError as e:
        L.logger.warn(e)
    except Exception as e:
        L.logger.exception(e)

if __name__ == "__main__":
    main()
