#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from common_import import *

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
