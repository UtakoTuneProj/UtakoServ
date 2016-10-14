# coding: utf-8
import urllib.request
import urllib.parse
import datetime
import json
import codecs
import re
import glob
import numpy as np

import UtakoServCore

gurl = urllib.request.urlretrieve

def make_chart(rankfilepass): #取得したランキングファイルからチャートを生成
    rankfile = codecs.open(rankfilepass,'r','utf-8')
    raw_rank = json.load(rankfile, encoding = 'utf-8')
    rankfile.close()
    rankdate = rankfilepass.split('\\')[-1].replace("Newest.json", "")

    chartfile = codecs.open("mvinfo/chart.json",'r','utf-8')
    chart = json.load(chartfile, encoding = 'utf-8')
    chartfile.close()

    for mvdata in raw_rank['data']:
        mvid = mvdata['contentId']
        [summ,dummy] = UtakoCore.predict(mvid)
        if summ > 0:
            if mvid not in chart:
                chart[mvid] = {'startTime' : nicodate2date12(mvdata['startTime'])}
            diffdt = time122datetime(rankdate) - time122datetime(chart[mvid]['startTime'])
            diffmin = diffdt.total_seconds()/60
            chart[mvid][diffmin] = {"viewCounter" : mvdata['viewCounter'], "commentCounter" : mvdata['commentCounter'], "mylistCounter" : mvdata['mylistCounter'] }
        else:
            if mvdata['contentId'] in chart:
                del chart[mvdata['contentId']]

    chartfile = codecs.open("mvinfo/chart.json",'w','utf-8')
    json.dump(chart, chartfile, ensure_ascii = False, indent = 2)
    chartfile.close()

def main():

if __name__ == '__main__':
    main()
