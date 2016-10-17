# coding: utf-8
import codecs
import json
import os

import UtakoServCore as core

learnFile = codecs.open("dat/chartlist.json",'r','utf-8')
learn_data = json.load(learnFile,encoding = 'utf-8')
learnFile.close()

for mov in learn_data:
    status = False
    if len(mov) == 25:
        for i,cell in enumerate(mov):
            if i != 24:
                if cell[0] < i*60 or cell[0] > (i+1)*60:
                    break
            else:
                if  < cell[0]

if __name__ == '__main__':
    pass
