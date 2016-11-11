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

import UtakoServCore as core

class ScreenerModel(ChainList):
    def __init__(self, n_units = 50, layer = 2):
        l = [L.Linear(98, n_units)]
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

def searchHit(query):#クエリに指定した検索結果の件数を返す:検索結果信用の基準は70程度

    if query.startswith("tag"):
        stag = cell.lstrip("tag")
        core.rankfilereq(searchtag = stag)
    else:
        stitle = cell.lstrip("title")
        core.rankfilereqTITLE(searchtitle = stitle)

    searchFile = codecs.open("ranking/0.json",'r','utf-8')
    search_data = json.load(searchFile, encoding = 'utf-8')
    searchFile.close()

    os.remove("ranking/0.json")
    return search_data["meta"]["totalCount"]

def teach(GUI = False):
    rankfilelist = [r.split('\\')[-1] for r in glob.glob("ranking/*Newest.json")]
    for i,rankdate in enumerate(rankfilelist):
        rankfilelist[i] =int( rankdate.replace("Newest.json", ""))
    latestrank = max(rankfilelist)

    jsonFile = codecs.open("ranking/"+str(latestrank)+"Newest.json",'r','utf-8')
    rankingArray = json.load(jsonFile,encoding = 'utf-8')
    jsonFile.close()

    for mv in rankingArray['data']:
        mvid = mv['contentId']
        teacher_req(mvid,GUI = GUI)

def teacher_req(mvid, GUI = False):
    teacherFile = codecs.open("Network/teacher.json",'r','utf-8')
    teacher_data = json.load(teacherFile,encoding = 'utf-8')
    teacherFile.close()

    if mvid not in teacher_data:
        movinforeq(mvid, Force = False)
        [pred,dummy] = predict(mvid)
        if abs(pred) < 0.5:
            print("ねえ、" + mvid + "がオリジナル曲かどうか調べてきてくれない?こんな動画なんだけど…")
            print(json.dumps(core.thumb_cook(mvid), ensure_ascii = False, indent = 2))
            print("オリジナル曲だった→1/じゃなかった→0/分からなかった→u/終わる→exit")
            res = input()
            if res == "1":
                print("ありがと、今から聞いてくるわ")
                teacher_data[mvid] = 1
            elif res == "0":
                print("そっか、残念ね…")
                teacher_data[mvid] = 0
            elif res == "exit":
                print("あんたはあたしと違って忙しいもんね")
                raise
            else:
                print("役立たずね")

    teacherFile = codecs.open("Network/teacher.json",'w','utf-8')
    json.dump(teacher_data,teacherFile,ensure_ascii = False)
    teacherFile.close()

def predict(mvid):

    MvInfo = thumb_cook(mvid)
    MvExist = {}
    for inTitle in MvInfo['title']:
        if "title"+inTitle not in learn_data:
            learn_data["title"+inTitle] = 0
        MvExist["title"+inTitle] = learn_data["title"+inTitle]
    for inTag in MvInfo['tags']:
        if "tag"+inTag not in learn_data:
            learn_data["tag"+inTag] = 0
        MvExist["tag"+inTag] = learn_data["tag"+inTag]
    summ = 0
    for w in MvExist:
        summ += float(MvExist[w])

    return summ,MvExist

def Perceptron(GUI = False):
    eta = 0.15

    teacherFile = codecs.open("Network/teacher.json",'r','utf-8')
    teacher_data = json.load(teacherFile,encoding = 'utf-8')
    teacherFile.close()

    combo = 0
    miss = 0

    while combo <= len(teacher_data):
        for oneteacher in teacher_data:

            [summ,MvExist] = predict(oneteacher)
            TeacherAns = teacher_data[oneteacher]

            if summ >= 0:
                studentAns = 1
            else:
                studentAns = 0
            if (studentAns != int(TeacherAns)):
                for Element in MvExist:
                    learn_data[Element] += (TeacherAns - studentAns) * eta
                miss += 1
                if not GUI:
                    print("Predict missed. Combo was "+ str(combo) +". miss is now "+str(miss)+". Changing Model...")
                combo = 0
            else:
                combo += 1
        if miss > 100000:
            break

    learnFile = codecs.open("Network/learned.json",'w','utf-8')
    json.dump(learn_data, learnFile, ensure_ascii = False, indent = 2)
    learnFile.close()

    return miss

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

if __name__ == '__main__'
    try:
        main(sys.argv[1])
    except ValueError:
        print("Command Line Argument '" + sys.argv[1] + "' is invalid.")
    except IndexError:
        print("Command Line Argument is needed.")
