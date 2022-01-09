#!/usr/bin/env python
# -*- mode: python -*- -*- coding: utf-8 -*-
import json
import urllib
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2
try:    
    import urlparse
except ImportError:
    from urllib.parse import urlparse
try:
    from urllib import urlencode
except:
    from urllib.parse import urlencode
import facebook

from config import (FACEBOOK_CONFIG, FACEBOOK_MANDEVILLA_CONFIG,
                    FACEBOOK_FIELDS)

##
## class
##

# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
# facebook
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
class BaseFaceBook(object):
    def __init__(self, object_id, token, version=None):
        self.object_id = object_id
        self.graph = facebook.GraphAPI(token, version=version)
        self.graph_url = 'https://graph.facebook.com/'
    
    def get_version(self):
        return self.graph.get_version()

    def get_object(self, object_id, extra=''):
        if not object_id:
            object_id = self.object_id
        return self.graph.get_object(object_id+extra)
    
    def get_albums(self, object_id=None, limit=None):
        if limit:
            option = '?limit=%s' % limit
        else:
            option = ''
        return self.get_object(object_id, '/albums'+option)

    def get_photos(self, object_id=None):
        return self.get_object(object_id, '/photos')

    def get_feed_legacy(self, mode='feed'):
        status = self.graph.get_connections(self.object_id, mode)
        return status
    
    def get_feed(self, args=FACEBOOK_FIELDS):
        fields = '/feed?fields=' + ','.join(args)
        return self.get_object(self.object_id, fields)
    
    def parse_feed(self, feed_data, fields=FACEBOOK_FIELDS):
        data_list = feed_data.get('data')
        for x in data_list:
            # check privacy
            privacy = x.get('privacy')
            if not privacy:
                continue
            if privacy.get('value') != 'EVERYONE':
                continue

            data = dict()
            for key in fields:
                if key == 'attachments':
                    attachments = x.get('attachments')
                    if not attachments:
                        continue
                    picture_list = []
                    for y in attachments['data']:
                        if y.get('media'):
                            picture = y['media']['image']
                        elif y.get('subattachments'):
                            picture = y['subattachments']['data'][0]['media']['image']
                        else:
                            continue
                        picture_list.append(picture)
                    data['pictures'] = picture_list
                elif key in ('likes', 'comments'):
                    tmp = x.get(key)
                    data[key] = tmp.get('data', []) if tmp else []
                else:
                    data[key] = x.get(key)
            yield data

    def post(self, message, mode='feed'):
        status = self.graph.put_object(self.object_id, mode, message=message)
        return status.get('id', None)
    
    def delete(self, object_id):
        try:
            self.graph.delete_object(object_id)
            return object_id
        except:
            pass

class FaceBook(BaseFaceBook):
    def __init__(self, object_id=FACEBOOK_CONFIG['user_id'],
                 token=FACEBOOK_CONFIG['user_token'],
                 version=FACEBOOK_CONFIG.get('version')):
        BaseFaceBook.__init__(self, object_id, token, version)
    
    def get_profile(self, object_id=None):
        return self.get_object(object_id)

    def get_profile_by_page(self, page_id):
        return self.get_profile(page_id)

    def get_friends(self):
        return self.graph.get_connections(self.object_id, 'friends')
    
class FaceBookPage(BaseFaceBook):
    def __init__(self, object_id, token, version, username):
        self.object_id = object_id
        self.token = token
        self.username = username
        BaseFaceBook.__init__(self, object_id, self.token, version)

    def get_likes(self, page_id):
        return self.get_summary(page_id, 'likes')
    
    def get_comments(self, page_id):
        return self.get_summary(page_id, 'comments')

    def get_summary(self, page_id, mode, args={'summary': True}):
        args.update({'access_token': self.token})
        result = urllib2.urlopen(self.graph_url + page_id + '/' + mode + "?" +
                                 urlencode(args)).read()
        try:
            return json.loads(result)
        except:
            return {}


class FBMandevilla(FaceBookPage):
    def __init__(self):
        FaceBookPage.__init__(self, object_id=FACEBOOK_MANDEVILLA_CONFIG['id'],
                              token=FACEBOOK_MANDEVILLA_CONFIG['access_token'],
                              version=FACEBOOK_CONFIG.get('version'),
                              username=FACEBOOK_MANDEVILLA_CONFIG['username'])

##
## functions
## 
def feed(url):
    data = feedparser.parse(url)
    for e in data['entries']:
        yield e
    
##
## test
##
##   $ nosetests -s --pdb webapi.py
##

# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
# facebook
# -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
def test_facebook():
    FB = FaceBook()
    assert True

def test_facebook_get_profile():
    FB = FaceBook()
    profile = FB.get_profile()
    assert profile.get('name') == 'Sumiya Sakoda'

def test_facebook_get_feed():
    FB = FaceBook()
    feed = FB.get_feed()
    assert feed.get('data')
    
def test_facebook_page_mandevilla_feed():
    FB = FBMandevilla()
    feed = FB.get_feed()
    assert feed.get('data')
    
def test_facebook_page_mandevilla_profile():
    FB = FaceBook()
    FBP = FBMandevilla()
    profile = FB.get_profile_by_page(FBP.object_id)

#def test_facebook_page_mandevilla_get_likes():
#    FB = FaceBook()
#    FBP = FBMandevilla()
#    profile = FB.get_profile_by_page(FBP.object_id)
#    likes = profile.get('likes')
#    assert likes

def test_facebook_page_mandevilla_post_delete():
    FBP = FBMandevilla()
    feed_id = FBP.post('test post page')
    result = FBP.delete(feed_id)
    assert feed_id == result

def test_facebook_parse_feed():
    FB = FBMandevilla()
    feed_data = FB.get_feed()
    data = FB.parse_feed(feed_data)
    assert list(data)    

##
## main
##
def cmd_facebook():
    FB = FaceBook()
    FBP = FBMandevilla()
    print (FB.get_profile())
    print (FB.get_friends())
    print (FB.get_profile_by_page(FBP.object_id))

def cmd_facebook_data(debug=True):
    import os
    from config import DATA_DIR
    FBP = FBMandevilla()

    # feed
    jsonfile = os.path.join(DATA_DIR, 'facebook_feed.json')
    if debug:
        feed_data = json.load(open(jsonfile, 'r'))        
    else:
        feed_data = FBP.get_feed()
        json.dump(feed_data, open(jsonfile, 'w'))
    """
    for x in feed_data['data']:
        print FBP.get_image_by_picture_url(x['picture'])
    """
    print (feed_data)

    # photo
    jsonfile = os.path.join(DATA_DIR, 'facebook_photo.json')
    if debug:
        photo_data = json.load(open(jsonfile, 'r'))
    else:
        photo_data = []
        for x in feed_data['data']:
            for y in FBP.get_image_by_link(x):
                photo_data.append(y)
        json.dump(photo_data, file(jsonfile,'w'))
    print (photo_data)

    # album
    """\
    ['count', 'likes', 'from', 'description', 'privacy', 'cover_photo', 'comments', 'updated_time', 'can_upload', 'place', 'location', 'created_time', 'link', 'type', 'id', 'name']
    """
    jsonfile = os.path.join(DATA_DIR, 'facebook_album.json')
    if debug:
        album_data = json.load(open(jsonfile, 'r'))
    else:
        album_data = FBP.get_albums()
        json.dump(album_data, file(jsonfile,'w'))
    #print album_data

if __name__ == "__main__":
    mode = 1
    if mode == 1:
        cmd_facebook()
    elif mode == 2:
        cmd_facebook_data()
    elif mode == 3:
        cmd_facebook_data(debug=False)
    else:
        pass
