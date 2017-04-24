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

import UtakoAnalyzer as analyzer
import sql
from tweepyCore import chart_tw

class MovDeletedException(Exception):
    def __init__(self,e):
        Exception.__init__(self,e)

class NoResponseException(Exception):
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

    def __repr__(self):
        return('{} <Utako Time Object>'.format(self.nico))

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
        for cell in mvidls:
            self.mvlist.append(cell)
            self.mvdate.append(start)

    def del_queue(self,queue):
        self.qcell.remove(queue)
        for cell in queue.list:
            i = self.mvlist.index(cell)
            del self.mvlist[i]
            del self.mvdate[i]

    def del_mv(self,mvid):
        start = self.mvdate.pop(self.mvlist.index(mvid))
        for q in self.qcell:
            if q.start == start:
                self[self.qcell.index(q)].q_delete(mvid)
                break
        self.mvlist.remove(mvid)

    def listate(self):
        return [x.queue for x in self.qcell]

class Chartcell:
    def __init__(self,l):
        self.view = l[1]
        self.comment = l[2]
        self.mylist = l[3]

        self.cm_cor = (self.view + self.mylist) / (self.view + self.comment + self.mylist)
        self.vocaran = self.view + self.comment * self.cm_cor + self.mylist ** 2 / self.view * 2
        self.vt30 = self.view + self.comment * self.cm_cor + self.mylist * 20
        self.vocasan = self.view + self.comment * 8 + self.mylist * 25

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

        for i in range(15): #15ページ目まで取得する
            rankfilereq(page = i)
            raw_rank = JSONfile("ranking/" + str(i) + ".json").data['data']
            for mvdata in raw_rank:
                mvid = mvdata['contentId']
                if not mvid in self.data.mvlist: #取得済みリストの中に含まれていないならば
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
        return None

    def tweet(self, hour, threshold):
        for mvid in self.data.qcell[-hour-1].list:
            y = analyzer.analyze(mvid)
            if type(y) == None:
                continue
            elif y.data[0][0] >= threshold:
                chart_tw(hour, y.data[0][0], mvid, MovInfo(mvid).title)

        return None

class Chartfile(JSONfile):
    #self.deletedlist:
    #self.update()
    def __init__(self, path = "dat/chartlist.json"):
        super().__init__(path)

    def update(self, queue, dltd = False):#queueで与えられた動画についてチャートを更新、削除された動画リストをself.deletedlistとして保持する
        self.deletedlist = []

        if not isinstance(queue, (tuple, list)):
            raise TypeError("queue must be list or tuple")
        for mvid in queue:
            try:
                movf = MovInfo(mvid)
            except MovDeletedException:
                if mvid in self.data:
                    del self.data[mvid]
                if not dltd:
                    self.deletedlist.append(mvid)
            else:
                movf.update()
                passedmin = (now.dt - movf.first_retrieve.dt).total_seconds() / 60
                gotdata = [
                           passedmin,
                           movf.view_counter,
                           movf.comment_num,
                           movf.mylist_counter
                          ]

                if mvid in self.data:
                    self.data[mvid].append(gotdata)
                else:
                    self.data[mvid] = [gotdata]

        self.write()

        return None

class InitChartfile(JSONfile):
    def __init__(self, encoding = 'utf-8'):
        super().__init__('dat/chartlist_init.json', encoding = encoding)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, d):
        self._data = d
        if len(d) == 0:
            [self.mvid, self.x, self.y] = [[],[],[]]
        else:
            [self.mvid, self.x, self.y] = list(zip(*d))
        self.write()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, d):
        self.vocaran = [Chartcell(e).vocaran for e in d]

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

class DataBase:
    def __init__(self):
        self.cursor = sql.cursor
        
    def _select(table, query):
        self.cursor.execute('SELECT %s from %s', (query, table))

    def _append(table, query):
        self.cursor.execute('INSERT into %s values %s', (table, query))

    def addChart(ID, epoch, Time, View, Comment, Mylist):
        q = '('
        for s in [ID, epoch, Time, View, Comment, Mylist]:
            q += str(s) + ','
        self._append('chart', q)
        
    def getChart(query):
        self._select('chart', q)
        return self.cursor.fetchall()

    def addIDtag(ID, tag):
        q = '(' + ID + ',' + tag + ')'
        self._append('IDtag', q)

    def getIDtag(query):
        self._select('IDtag', q)
        return self.cursor.fetchall()

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

def main():
    qf = Queuefile()
    qf.update()
    cf = Chartfile()
    cf.update(qf.todays_mv)
    cf.update(qf.lastwks_mv, dltd = True)
    qf.delete(cf.deletedlist)
    qf.tweet(24, 300)

    return None

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='UTF-8')
gurl = urllib.request.urlretrieve
now = Time(mode = 'now')
if __name__ == '__main__':
    main()
