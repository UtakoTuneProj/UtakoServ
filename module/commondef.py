#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import urllib.error
import datetime
import json
import codecs
import xml.etree.ElementTree as ET
import re
import os

class Time:
    def __init__(self, mode = "now", stream = None):
        if mode == "now":
            self.dt = datetime.datetime.now()
        elif mode in ["nico","n"]:
            self.dt = self.__n2d(stream)
        elif mode in ["str12","str","s"]:
            self.dt = self.__s2d(stream)
        elif mode in ["datetime","dt","d"]:
            self.dt = stream
        else:
            raise ValueError
        self.nico = self.__d2n(self.dt)
        self.str12 = self.__d2s(self.dt)
        return None

    def __repr__(self):
        return('{} <Utako Time Object>'.format(self.nico))

    def __n2d(self,nicodate): #ニコ動形式の時刻をPython内部時刻形式に変換
        return datetime.datetime.strptime(nicodate,"%Y-%m-%dT%H:%M:%S+09:00")

    def __s2d(self,time12): #12桁時刻方式をPython内部時刻形式に変換
        return datetime.datetime.strptime(time12,"%Y%m%d%H%M")

    def __d2s(self,dt): #Python内部時刻形式を12桁時刻方式に変換
        return dt.strftime("%Y%m%d%H%M")

    def __d2n(self,dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

class JSONfile:
    #self.path:ファイルパスを保存
    #self.encoding:エンコードを保存
    #self.data:データを保存
    #
    #self.read():self.pathのファイルから読み込む関数
    #self.write(indent):self.dataを書き込む関数
    def __init__(self, path, encoding = 'utf-8'):
        self.path = path
        self.encoding = encoding
        self.data = self.read()
    def read(self):
        fobj = codecs.open(self.path,'r',self.encoding)
        stream = json.load(fobj, encoding = self.encoding)
        fobj.close()
        return stream
    def write(self, indent = False, compress = True):
        fobj= codecs.open(self.path,'w',self.encoding)
        if indent and compress:
            json.dump(float_compressor(self.data), fobj, ensure_ascii = False, indent = 2)
        elif indent:
            json.dump(self.data, fobj, ensure_ascii = False, indent = 2)
        elif compress:
            json.dump(float_compressor(self.data), fobj, ensure_ascii = False)
        else:
            json.dump(self.data, fobj, ensure_ascii = False)

        fobj.close()
        return None

class MovInfo:
    def __init__(self, mvid):
        self.mvid = mvid
        self.fname = 'getthumb/' + mvid + '.xml'
        if not os.path.exists(self.fname):
            self.update()
        else:
            self.read()

    def update(self): #動画情報xmlを取得
        try:
            gurl("http://ext.nicovideo.jp/api/getthumbinfo/" + self.mvid ,self.fname)
        except:
            raise NoResponseException("Cannot get thumbs for " + self.mvid)

        self.read()
        return None

    def read(self):#ニコ動動画詳細xml形式を辞書形式に
        with codecs.open(self.fname, 'r', 'utf-8') as f:
            root = ET.parse(f).getroot()
        if root.attrib['status'] == 'fail':
            raise MovDeletedException(self.mvid + ' has been deleted.')

        for child in root[0]:#xmlの辞書化
            if child.tag == 'tags':
                setattr(self, 'tags', [x.text for x in child])
            elif child.tag in ["mylist_counter", "comment_num", "view_counter"]:#一部を数値に変換
                setattr(self, child.tag, int(child.text))
            elif child.tag == 'first_retrieve':
                self.first_retrieve = Time(stream = child.text, mode = 'nico')
            else:
                setattr(self, child.tag, child.text)

        # http://www.lifewithpython.com/2014/08/python-use-multiple-separators-to-split-strings.html
        self.title_split = [x for x in re.split("[/\[\]【】\u3000〔〕／〈〉《》［］『』「」≪≫＜＞]",self.title) if len(x) > 0] #指定文字でタイトルを分割

        return None

def float_compressor(obj):
    if isinstance(obj, float):
        return round(obj,2)
        # return CompressedFloat(obj)
    elif isinstance(obj, dict):
        return dict((k, float_compressor(v)) for k, v in obj.items())
    elif isinstance(obj,(list,tuple)):
        return list(map(float_compressor, obj))
    else:
        return obj

def rankfilereq(searchtag = "VOCALOID", page = 0): #searchtagに指定したタグのランキングを取得、指定のない場合はVOCALOIDタグ
    rankreqbase = "http://api.search.nicovideo.jp/api/v2/video/contents/search?q=" + urllib.parse.quote(searchtag) + "&targets=tags&fields=contentId,title,tags,categoryTags,viewCounter,mylistCounter,commentCounter,startTime&_sort=-startTime&_offset=" + str(page * 100) + "&_limit=100&_context=UtakoOrihara(VocaloidRankingBot)"

    try:
        gurl(rankreqbase, "ranking/" + str(page) + ".json")
    except urllib.error.URLError:
        print("Search query for",searchtag,"is failed. Maybe overloaded.")

    return None

def rankfilereqTITLE(searchtitle = "VOCALOID", page = 0): #searchtitleに指定したタイトルのランキングを取得、指定のない場合は"VOCALOID"
    rankreqbase = "http://api.search.nicovideo.jp/api/v2/video/contents/search?q=" + urllib.parse.quote(searchtitle) + "&targets=title&fields=contentId,title,tags,categoryTags,viewCounter,mylistCounter,commentCounter,startTime&_sort=-startTime&_offset=" + str(page * 100) + "&_limit=100&_context=UtakoOrihara(VocaloidRankingBot)"

    gurl(rankreqbase, "ranking/" + str(page) + ".json")

    return None

gurl = urllib.request.urlretrieve
now = Time(mode = 'now')
