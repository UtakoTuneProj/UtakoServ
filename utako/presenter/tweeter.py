#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# twitter core module
#http://statsbeginner.hatenablog.com/entry/2015/10/21/131717
from utako.common_import import *

class Tweeter:

    def __init__(self, **kwargs):
        API_KEY = '***REMOVED***'
        API_SECRET = '***REMOVED***'
        ACCESS_TOKEN = '***REMOVED***'
        ACCESS_SECRET = '***REMOVED***'
        self.auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

    def __call__(self, mvid, title, stage, est):
        content = '[予想スコア:{0:.1f}pts / {1:.0f}時間経過]\n{2}\nhttp://nico.ms/{3} #{3}'.format(est, stage, title, mvid)
        tweepy.API(self.auth).update_status(content)
