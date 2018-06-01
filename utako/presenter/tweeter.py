#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# twitter core module
#http://statsbeginner.hatenablog.com/entry/2015/10/21/131717
from utako.common_import import *

class Tweeter:

    def __init__(self, **kwargs):
        API_KEY = 'nS4Ypx9b0Pz06bTG0PM2E3ZSy'
        API_SECRET = 'iLZ8GteNsu54l8rPfzR5R9XuHfNW0lHS7y5jtKiqYUaqvjhgb8'
        ACCESS_TOKEN = '784080809556783104-7mb9n1FyYhSLc0Kgywteo2SgUY7FBl0'
        ACCESS_SECRET = 'qEzlSntx3Gy3nztI3EvlsxhHcagdQJ5rQMCJj9o8vHKGu'
        self.auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

    def __call__(self, mvid, title, stage, est):
        content = '[予想スコア:{0:.1f}pts / {1:.0f}時間経過]\n{2}\nhttp://nico.ms/{3} #{3}'.format(est, stage, title, mvid)
        tweepy.API(self.auth).update_status(content)
