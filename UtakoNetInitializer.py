# coding: utf-8
import codecs
import json
import os

import UtakoServCore as core

learnFile = codecs.open("Network/learned.json",'r','utf-8')
learn_data = json.load(learnFile,encoding = 'utf-8')
learnFile.close()

res = []

resFile = codecs.open("Network/searchResult.json",'r','utf-8')
gotres = json.load(resFile, encoding = 'utf-8')
resFile.close()

flattenres = []
ex = flattenres.extend
for s in gotres:
    ex(s)

for i,cell in enumerate(learn_data):
    print(i)

    if cell not in flattenres:
        if cell.startswith("tag"):
            stag = cell.lstrip("tag")
            print("tag")
            print(stag)
            core.rankfilereq(searchtag = stag)
        else:
            stitle = cell.lstrip("title")
            print("title")
            print(stitle)
            core.rankfilereqTITLE(searchtitle = stitle)


        searchFile = codecs.open("ranking/0.json",'r','utf-8')
        search_data = json.load(searchFile, encoding = 'utf-8')
        searchFile.close()

        res.append([cell,search_data["meta"]["totalCount"]])

        os.remove("ranking/0.json")

if __name__ == '__main__':
    pass
