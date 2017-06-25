# coding:utf-8
# twitter core module
#http://statsbeginner.hatenablog.com/entry/2015/10/21/131717
import tweepy
from configparser import ConfigParser

from loginit import *
logger = getLogger(__name__)

conf = ConfigParser()
conf.read('conf/auth.conf')

auth = tweepy.OAuthHandler(
    conf['tweepy']['API_KEY'],
    conf['tweepy']['API_SECRET']
)
auth.set_access_token(
    conf['tweepy']['ACCESS_TOKEN'],
    conf['tweepy']['ACCESS_SECRET']
)

api = tweepy.API(auth)
tweet = lambda x:api.update_status(status = x)

def chart_tw(stage,est,mvid,title):
    content = '[予想スコア:{0:.1f}pts / {1:.0f}時間経過]\n{2}\nhttp://nico.ms/{3} #{3}'.format(est, stage, title, mvid)
    tweet(content)
