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
        return None

    def __n2d(self,nicodate): #ニコ動形式の時刻をPython内部時刻形式に変換
        return datetime.datetime.strptime(nicodate,"%Y-%m-%dT%H:%M:%S+09:00")

    def __s2d(self,time12): #12桁時刻方式をPython内部時刻形式に変換
        return datetime.datetime.strptime(time12,"%Y%m%d%H%M")

    def __d2s(self,dt): #Python内部時刻形式を12桁時刻方式に変換
        return dt.strftime("%Y%m%d%H%M")

    def __d2n(self,dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%S+09:00")

class Queuecell:
    def __init__(self,queue):
        self.queue = queue

    @property
    def queue(self):
        return self._queue

    @queue.setter
    def queue(self, queue):
        self._queue = queue
        self.start = queue['start']
        self.list = queue['list']

    def q_delete(self,mvid):
        self.queue['list'].remove(mvid)

class Queue:
    def __init__(self, queuels):
        self.qcell = []
        self.mvlist = []
        self.mvdate = []
        for q in queuels:
            self.qcell.append(Queuecell(q))
            for cell in q['list']:
                self.mvlist.append(cell)
                self.mvdate.append(q['start'])

    def add_queue(self,start,mvidls):
        self.qcell.append(Queuecell({'start':start, 'list':mvidls}))

    def del_queue(self,queue):
        self.qcell.remove(queue)

    def del_mv(self,mvid):
        start = self.mvdate.pop(self.mvlist.index(mvid))
        for q in self.qcell:
            if q.start == start:
                self[self.qcell.index(q)].q_delete(mvid)
                break
        self.mvlist.remove(mvid)

    def listate(self):
        return [x.queue for x in self.qcell]

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

class Queuefile(JSONfile):
    def __init__(self, path = "dat/queuelist.json"):
        super().__init__(path = path)
        self.data = Queue(self.data)

    def write(self):
        _tmp = self.data
        self.data = self.data.listate()
        super().write()
        self.data = _tmp

    def update(self): #ランキング取得・キュー生成部

        newcomer = []
        exitstatus = False

        for i in range(15):
            rankfilereq(page = i)
            raw_rank = JSONfile("ranking/" + str(i) + ".json").data['data']
            for mvdata in raw_rank:
                mvid = mvdata['contentId']
                if not mvid in self.data.mvlist: #最後に取得できたリストの中に含まれていないならば
                    newcomer.append(mvid)
                else:
                    break
            else:
                continue
            break

        for j in range(i+1):
            os.remove("ranking/" + str(j) + ".json")

        self.data.add_queue(now.str12,newcomer)
        self.todays_mv = []
        self.lastwks_mv = []

        for raw_queue in self.data.qcell:
            postdate = Time(mode = "s", stream = raw_queue.start)
            if now.dt - postdate.dt < datetime.timedelta(days = 1): #startが1日以内ならば
                self.todays_mv.extend(raw_queue.list)
            elif now.dt - postdate.dt > datetime.timedelta(days = 7): #startが7日以前ならば
                self.lastwks_mv.extend(raw_queue.list)
                self.data.del_queue(raw_queue)

        self.write()

        return None

    def delete(self, deleted):
        for d in deleted:
            self.data.del_mv(d)
        self.write()

class Chartfile(JSONfile):
    #self.deletedlist:
    #self.update()
    def __init__(self, path = "dat/chartlist.json"):
        super().__init__(path = path)

    def update(self, queue):#queueで与えられた動画についてチャートを更新、削除された動画リストが返ってくる
        self.deletedlist = []

        if not isinstance(queue, (tuple, list)):
            raise TypeError("queue must be list or tuple")
        for mvid in queue:
            movinforeq(mvid)
            try:
                mvinfo = thumb_cook(mvid)
            except MovDeletedException:
                if mvid in self.data:
                    del self.data[mvid]
                self.deletedlist.append(mvid)
            else:
                postdate = Time(mode = 'n', stream = mvinfo['first_retrieve'])
                passedmin = (now.dt - postdate.dt).total_seconds() / 60
                gotdata = [passedmin, mvinfo['view_counter'], mvinfo['comment_num'], mvinfo['mylist_counter']]

                if mvid in self.data:
                    self.data[mvid].append(gotdata)
                else:
                    self.data[mvid] = [gotdata]

        self.write()

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

def movinforeq(mvid): #動画情報xmlを取得

    try:
        gurl("http://ext.nicovideo.jp/api/getthumbinfo/" + mvid ,"getthumb/"+ str(mvid) +".xml")
    except:
        raise MovDeletedException("handling" + mvid + "error occured")

    return None

def rankfilereq(searchtag = "VOCALOID", page = 0): #searchtagに指定したタグのランキングを取得、指定のない場合はVOCALOIDタグ
    rankreqbase = "http://api.search.nicovideo.jp/api/v2/video/contents/search?q=" + urllib.parse.quote(searchtag) + "&targets=tags&fields=contentId,title,tags,categoryTags,viewCounter,mylistCounter,commentCounter,startTime&_sort=-startTime&_offset=" + str(page * 100) + "&_limit=100&_context=UtakoOrihara(VocaloidRankingBot)"

    gurl(rankreqbase, "ranking/" + str(page) + ".json")

    return None

def rankfilereqTITLE(searchtitle = "VOCALOID", page = 0): #searchtitleに指定したタイトルのランキングを取得、指定のない場合はVOCALOIDタグ
    rankreqbase = "http://api.search.nicovideo.jp/api/v2/video/contents/search?q=" + urllib.parse.quote(searchtitle) + "&targets=title&fields=contentId,title,tags,categoryTags,viewCounter,mylistCounter,commentCounter,startTime&_sort=-startTime&_offset=" + str(page * 100) + "&_limit=100&_context=UtakoOrihara(VocaloidRankingBot)"

    gurl(rankreqbase, "ranking/" + str(page) + ".json")

    return None

def main():
    qf = Queuefile()
    qf.update()
    cf = Chartfile()
    cf.update(qf.todays_mv)
    cf.update(qf.lastwks_mv)
    qf.delete(cf.deletedlist)
    # rankreq()
    # postdaychk()
    # aweekafterchk()

    return None

if __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='UTF-8')
    gurl = urllib.request.urlretrieve
    now = Time(mode = 'now')
    main()
