# coding: utf-8
import codecs
import json
import os

import UtakoServCore as core

learnFile = codecs.open("Network/searchResult.json",'r','utf-8')
learn_data = json.load(learnFile,encoding = 'utf-8')
learnFile.close()

res = []
th = 70
for cell in learn_data:
    if cell[1] > th:
        res.append(cell)

learnFile = codecs.open("Network/NewResult.json",'w','utf-8')
json.dump(res, learnFile, ensure_ascii = False, indent = 2)
learnFile.close()

if __name__ == '__main__':
    pass
