# coding: utf-8
import codecs
import json
import os

import UtakoServCore as core

learnFile = codecs.open("Network/searchResult.json",'r','utf-8')
learn_data = json.load(learnFile,encoding = 'utf-8')
learnFile.close()

if __name__ == '__main__':
    pass
