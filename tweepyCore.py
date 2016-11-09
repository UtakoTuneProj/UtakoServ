# coding:utf-8

#http://statsbeginner.hatenablog.com/entry/2015/10/21/131717
import tweepy

API_KEY = '***REMOVED***'
API_SECRET = '***REMOVED***'
auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
ACCESS_TOKEN = '***REMOVED***'
ACCESS_SECRET = '***REMOVED***'
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

api = tweepy.API(auth)
tweet = lambda x:api.update_status(status = x)
