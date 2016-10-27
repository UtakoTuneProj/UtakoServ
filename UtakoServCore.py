# coding: utf-8
import urllib.request
import urllib.parse
import datetime
import json
import codecs
import sys
import io
import xml.etree.ElementTree as ET
import re
import glob
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='UTF-8')
gurl = urllib.request.urlretrieve

class MovDeletedException(Exception):
    def __init__(self,e):
        Exception.__init__(self,e)

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

    def __n2d(self,nicodate): #ニコ動形式の時刻をPython内部時刻形式に変換
        return datetime.datetime.strptime(nicodate,"%Y-%m-%dT%H:%M:%S+09:00")

    def __s2d(self,time12): #12桁時刻方式をPython内部時刻形式に変換
        return datetime.datetime.strptime(time12,"%Y%m%d%H%M")

    def __d2s(self,dt): #Python内部時刻形式を12桁時刻方式に変換
        return dt.strftime("%Y%m%d%H%M")

    def __d2n(self,dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")

class JSONfile:
    def __init__(self, path, encoding = 'utf-8'):
        self.path = path
        self.encoding = encoding
    def read(self):
        fobj = codecs.open(self.path,'r',self.encoding)
        stream = json.load(fobj, encoding = self.encoding)
        fobj.close()
        return stream
    def write(self, stream, indent = False):
        fobj= codecs.open(self.path,'w',self.encoding)
        if indent:
            json.dump(stream, fobj, ensure_ascii = False, indent = 2)
        else:
            json.dump(stream, fobj, ensure_ascii = False)
        fobj.close()
        return None

now = Time(mode = 'now')

def xml2dict(filename):#ニコ動動画詳細xml形式を辞書形式に
    page = {}
    tree = ET.parse(filename)
    root = tree.getroot()
    if root.attrib['status'] == 'fail':
        raise MovDeletedException(filename + 'is info for deleted movie.')

    for child in root[0]:#xmlの辞書化
        page[child.tag] = child.text

    page["tags"] = []#タグの分割
    for tags in root[0].find("tags"):
        page["tags"].append(tags.text)

    return page

#https://remotestance.com/blog/136/
def thumb_cook(mvid):#mvidについて取得済みのxmlファイルを解析し整形

    page = xml2dict("getthumb/"+mvid+".xml")

    for deletetag in ["watch_url", "movie_type", "size_low", "no_live_play", "embeddable", "last_res_body", "user_icon_url", "size_high", "thumb_type"]:#不必要なエントリを除去
        if deletetag in page:
            del page[deletetag]

    for s2i in ["mylist_counter", "comment_num", "view_counter"]:#一部を数値に変換
        page[s2i] = int(page[s2i])

    # http://www.lifewithpython.com/2014/08/python-use-multiple-separators-to-split-strings.html
    page["title"] = [x for x in re.split("[/\[\]【】\u3000〔〕／〈〉《》［］『』「」≪≫＜＞]",page["title"]) if len(x) > 0] #指定文字でタイトルを分割

    return page

def movinforeq(mvid,Force = False): #動画情報xmlがない場合は取得、Force=Trueで強制取得
    try:
        open("getthumb/"+mvid+".xml")
        if Force :
            gurl("http://ext.nicovideo.jp/api/getthumbinfo/" + mvid ,"getthumb/"+ str(mvid) +".xml")

    except FileNotFoundError:
        gurl("http://ext.nicovideo.jp/api/getthumbinfo/" + mvid , "getthumb/"+ str(mvid) +".xml")

    return None

def rankfilereq(searchtag = "VOCALOID", page = 0): #searchtagに指定したタグのランキングを取得、指定のない場合はVOCALOIDタグ
    rankreqbase = "http://api.search.nicovideo.jp/api/v2/video/contents/search?q=" + urllib.parse.quote(searchtag) + "&targets=tags&fields=contentId,title,tags,categoryTags,viewCounter,mylistCounter,commentCounter,startTime&_sort=-startTime&_offset=" + str(page * 100) + "&_limit=100&_context=UtakoOrihara(VocaloidRankingBot)"

    gurl(rankreqbase, "ranking/" + str(page) + ".json")

    return None

def rankfilereqTITLE(searchtitle = "VOCALOID", page = 0): #searchtitleに指定したタイトルのランキングを取得、指定のない場合はVOCALOIDタグ
    rankreqbase = "http://api.search.nicovideo.jp/api/v2/video/contents/search?q=" + urllib.parse.quote(searchtitle) + "&targets=title&fields=contentId,title,tags,categoryTags,viewCounter,mylistCounter,commentCounter,startTime&_sort=-startTime&_offset=" + str(page * 100) + "&_limit=100&_context=UtakoOrihara(VocaloidRankingBot)"

    gurl(rankreqbase, "ranking/" + str(page) + ".json")

    return None

def rankreq(): #ランキング取得・キュー生成部
    listfile = JSONfile("dat/queuelist.json")
    queuelist = listfile.read()

    i = -1
    while True:
        latestList = queuelist[i]['list']
        i -= 1
        if len(latestList) != 0:
            break

    newcomer = []
    i = 0
    exitstatus = False

    while True:
        rankfilereq(page = i)

        rankfile = JSONfile("ranking/" + str(i) + ".json")
        raw_rank = rankfile.read()

        for mvdata in raw_rank['data']:
            mvid = mvdata['contentId']
            mvdt = mvdata['startTime']
            if not mvid in latestList: #最後に取得したリストの中に含まれていないならば
                newcomer.append(mvid)
            else:
                exitstatus = True
                break

        if exitstatus or i == 14:
            break
        else:
            i += 1

    queuelist.append({"start":now.str12, "list": newcomer})

    for j in range(i+1):
        os.remove("ranking/" + str(j) + ".json")

    listfile.write(queuelist)
    return None

def chartupdate(queue):#queueで与えられた動画についてチャートを更新、削除された動画リストが返ってくる
    listfile = JSONfile("dat/chartlist.json")
    chartlist = listfile.read()

    deletedlist = []

    for mvid in queue:
        movinforeq(mvid, Force = True)
        try:
            mvinfo = thumb_cook(mvid)
        except MovDeletedException:
            if mvid in chartlist:
                del chartlist[mvid]
            deletedlist.append(mvid)
        else:
            postdate = Time(mode = 'n', stream = mvinfo['first_retrieve'])
            passedmin = (now.dt - postdate.dt).total_seconds() / 60
            gotdata = [round(passedmin,1), mvinfo['view_counter'], mvinfo['comment_num'], mvinfo['mylist_counter']]

            if mvid in chartlist:
                chartlist[mvid].append(gotdata)
            else:
                chartlist[mvid] = [gotdata]

    listfile.write(chartlist)

    return deletedlist

def postdaychk(): #投稿日チェック
    listfile = JSONfile("dat/queuelist.json")
    queuelist = listfile.read()

    queue = []

    for raw_queue in queuelist:
        postdate = Time(mode = "s", stream = raw_queue['start'])
        if now.dt - postdate.dt < datetime.timedelta(days = 1): #startが1日以内ならば
            queue.extend(raw_queue['list'])

    deleted = chartupdate(queue)
    for mvid in deleted:
        os.remove("getthumb/" + mvid + ".xml")

def aweekafterchk(): #一週間後チェック
    listfile = JSONfile("dat/queuelist.json")
    queuelist = listfile.read()

    queue = []

    for raw_queue in queuelist:
        postdate = Time(mode = "s", stream = raw_queue['start'])
        if now.dt - postdate.dt > datetime.timedelta(days = 7): #startが7日以前ならば
            queue.extend(raw_queue['list'])
            queuelist.remove(raw_queue)

    chartupdate(queue)
    for mvid in queue:
        os.remove("getthumb/" + mvid + ".xml")

    listfile.write(queuelist)

def main():
    rankreq()
    postdaychk()
    aweekafterchk()

if __name__ == '__main__':
    main()
