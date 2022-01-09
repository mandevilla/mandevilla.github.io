#!/usr/bin/env python
# -*- mode: python -*- -*- coding: utf-8 -*-
import os
import sys

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from config import PY3, THUMBNAIL_CROP_SIZE, DATA_DIR, FACEBOOK_IMAGE_DIR, \
     BANNER_X_POSITION, BANNER_Y_POSITION, BANNER_COLOR, BANNER_FONT, \
     BANNER_FONT_SIZE

if PY3:
    from io import StringIO
    import urllib.request as urllib2
else:
    from cStringIO import StringIO
    import urllib2
    

TEST_URL = 'https://fbcdn-photos-b-a.akamaihd.net/hphotos-ak-frc3/t1.0-0/10256479_1520285324865266_6279321579780439586_n.jpg'
IMAGE_DIR = os.path.join(DATA_DIR, 'image')
TEST_FILENAME = os.path.join(IMAGE_DIR, 'test.jpg')
TEST_IMAGE = os.path.join(IMAGE_DIR, 'download.jpg')

##
## function
##
def open_image(filename):
    return Image.open(filename)

def crop_image(image_object, size):
    width, height = image_object.size
    diff = abs(width - height) / 2
    base = min(width, height)
   
    if width > height:
        box = (diff, 0, base+diff, base)
    else:
        box = (0, diff, base, base+diff)

    return image_object.crop(box)

def make_thumb(image_object, size, crop, algorithm=Image.ANTIALIAS):
    if crop:
        image_object = crop_image(image_object, size)
        
    image_object.thumbnail((size, size), algorithm)

    return image_object

def download_image(url, filename, size=0, rewrite=False, crop=False):
    if not rewrite:
        if os.path.exists(filename):
            return False
    image_object = StringIO(urllib2.urlopen(url).read())
    im = Image.open(image_object)

    if size:
        im = make_thumb(im, size, crop)

    im.save(filename)
    return im

def make_thumb_via_url(url, filename, size=THUMBNAIL_CROP_SIZE, rewrite=False,
                       crop=True):
    try:
        im = download_image(url, filename, size, rewrite, crop)
        return True
    except:
        return False

def insert_text(original_image, save_image, text, pos_x=BANNER_X_POSITION,
                pos_y=BANNER_Y_POSITION, color=BANNER_COLOR,
                font_name=BANNER_FONT, font_size=BANNER_FONT_SIZE):
    im = Image.open(original_image)
    text_inserted = False
    draw = ImageDraw.Draw(im)
    if font_name:
        dirs = ('/usr/share/fonts/bitstream-vera/',
                '/usr/share/fonts/truetype/ttf-bitstream-vera/',
                '/usr/X11R6/lib/X11/fonts/TTF/',
                'C:\\Windows\\Fonts')
        for d in dirs:
            fontpath = os.path.join(d, font_name)
            if os.path.exists(fontpath):
                font = ImageFont.truetype(fontpath, font_size)
                draw.text((pos_x, pos_y), text, font=font, fill=color)
                text_inserted = True
    if not text_inserted:
        draw.text((pos_x, pos_y), text, fill=color)
    im.save(save_image)
    return True
              
##
## test
## 
##   $ nosetests -s --pdb image.py
##
def test_open_image():
    assert open_image(TEST_IMAGE)

def test_crop_image():
    image_object = open_image(TEST_IMAGE)
    image_object = crop_image(image_object, 10)
    assert image_object

def test_make_thumb():
    image_object = open_image(TEST_IMAGE)
    image_object = make_thumb(image_object, 10, False)
    assert image_object

"""
def test_make_thumb_via_url():
    filename = os.path.join(FACEBOOK_IMAGE_DIR, TEST_FILENAME)
    result = make_thumb_via_url(TEST_URL, filename, rewrite=True)
    assert result
    im = Image.open(filename)
    assert max(im.size) <= THUMBNAIL_CROP_SIZE
"""

def test_insert_text():
    original_image = os.path.join(IMAGE_DIR, 'banner_facebook.png')
    save_image = os.path.join(IMAGE_DIR, 'facebook_test.jpg')
    assert insert_text(original_image, save_image, 'pluto')
    #os.unlink(save_image)

##
## main
##
def cmd_make_thumb():
    make_thumb_via_url(TEST_URL, TEST_IMAGE)

def cmd_image_text():
    original_image = os.path.join(IMAGE_DIR, 'banner_facebook.png')
    save_image = os.path.join(IMAGE_DIR, 'facebook.jpg')
    insert_text(original_image, save_image, '1188 likes')

def main(argv):
    cmd_make_thumb()
    cmd_image_text()
    
if __name__ == "__main__":
    main(sys.argv)
