#!/usr/bin/env python
# -*- mode: python -*- -*- coding: utf-8 -*-

WEEK_MAP = (u'月', u'火', u'水', u'木', u'金', u'土', u'日')

def parse_json(url):
    try:
        return json.loads(urllib2.urlopen(url).read())
    except urllib2.HTTPError as e:
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
