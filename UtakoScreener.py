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
from chainer import cuda, Variable, optimizers, Chain, ChainList
import chainer.functions  as F
import chainer.links as L
import numpy as np

import UtakoServCore as core

class ScreenerModel(ChainList):
    def __init__(self, in_len, n_units = 50, layer = 2):
        l = [L.Linear(98, n_units)]
        if layer > 2:
            l.extend([L.Linear(n_units, n_units) for x in range(layer - 2)])
        l.append(L.Linear(n_units, 1))
        super().__init__(*l)

    def __call__(self, x):
        h = x
        for i in range(self.__len__() - 1):
            layer = self.__getitem__(i)
            h = F.relu(layer(h))
        o_layer = self.__getitem__(i+1)
        return o_layer(h)

    def error(self, x_data, y_data, train = True):
        y = self(Variable(x_data))
        t = Variable(y_data)
        if not train:
            ret = [t.data[0][0], y.data[0][0]]
        else:
            ret = None

        return F.mean_squared_error(y,t), ret

class TeacherFile(core.JSONfile):
    def __init__(self, path = "Network/teacher.json"):
        super().__init__(path = path)

class CorrtableFile(core.JSONfile):
    def __init__(self, path = "Network/corr_table.json"):
        super().__init__(path = path)
        self.len = len(self.data)

    def thumb2chainer(self, *keys):
        ret = [0 for x in range(self.len)]
        for key in keys:
            if key in self.data:
                ret[self.data.index(key)] = 1
            else:
                self.data.append(key)
                self.len += 1
                ret.append(1)

        return np.array(ret, dtype = np.float32)

def searchHit(query):#クエリに指定した検索結果の件数を返す:検索結果信用の基準は70程度

    if query.startswith("tag"):
        stag = cell.lstrip("tag")
        core.rankfilereq(searchtag = stag)
    else:
        stitle = cell.lstrip("title")
        core.rankfilereqTITLE(searchtitle = stitle)

    searchFile = core.JSONfile("ranking/0.json")
    ret = searchFile.data["meta"]["totalCount"]

    del searchFile
    os.remove("ranking/0.json")
    return ret

def teach():
    chartf = core.Chartfile()
    teacherf = TeacherFile()
    corrtablef = CorrtableFile()
    net = ScreenerModel(in_len = corrtablef.len)

    for mv in chartf.data.keys():

        if mvid not in teachef.data:
            thumb = core.MovInfo(mvid)
            thumb.update()

            x = corrtablef.thumb2chainer(*thumb.tags)

            pred = net(x)
            if abs(pred) < 0.5:
                print("ねえ、" + mvid + "がオリジナル曲かどうか調べてきてくれない?こんな動画なんだけど…")
                for tk in thumb.data.keys():
                    print(tk + ':' + thumb.data[tk])
                print(pred)
                print("オリジナル曲だった→1/じゃなかった→0/分からなかった→u/終わる→exit")
                res = input()
                if res == "1":
                    print("ありがと、今から聞いてくるわ")
                    teacherf.data[mvid] = 1
                elif res == "0":
                    print("そっか、残念ね…")
                    teacherf.data[mvid] = 0
                elif res == "exit":
                    print("あんたはあたしと違って忙しいもんね")
                    break
                else:
                    print("役立たずね")

    teacherf.write()
    corrtablef.write()

def learn():
    pass

def main(mode):
    if mode == "teach":
        teach()
    elif mode == "learn":
        learn()
    elif mode in "all":
        teach()
        learn()
    else:
        raise ValueError()

if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except ValueError:
        print("Command Line Argument '" + sys.argv[1] + "' is invalid.")
    except IndexError:
        print("Command Line Argument is needed.")
