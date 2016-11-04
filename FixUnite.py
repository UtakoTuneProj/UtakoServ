# coding: utf-8
import codecs
import json

import UtakoServCore as core

def screen(chart, new):

    chart.extend(new)
    ret = []
    j = 0
    for c,cell in enumerate(chart):
        i = c - j
        if i < 24 and (cell[0] < i*60 or ((i+1) * 60 + 30 < cell[0])):
            j += 1
        elif i == 24 and (cell[0] < 10140 or 10200 + 30 < cell[0]):
            j += 1
        elif i > 24:
            break
        else:
            ret.append(cell)

    return ret

def unite():

    chartold = core.Chartfile('dat/chartlist.old.json')
    chartnew = core.Chartfile('dat/chartlist.new.json')
    chartunite = core.Chartfile()
    name = ['Legacy', 'Oldest', '--------', 'Dual', 'Error', 'After-01', 'After-02', 'New', 'Newest']
    counter = [0 for i in range(9)]

    for mvid in chartnew.data.keys():
        if mvid not in chartold.data: #Fix02より新しい(Newest)
            chartunite.data[mvid] = chartnew.data[mvid]
            status = 8

        elif len(chartnew.data[mvid]) \
           - len(chartold.data[mvid]) \
          == 12: #Fix02の12時間以内に取得(New)
            chartunite.data[mvid] = chartnew.data[mvid]
            status = 7

        elif len(chartnew.data[mvid]) == 24: #Error以降Fix02以前に取得(After-02)
            chartunite.data[mvid] = chartnew.data[mvid]
            status = 6

        elif len(chartold.data[mvid]) == 24 \
         and len(chartnew.data[mvid]) == 25: #Error以降Fix02以前に取得(After-01)
            chartunite.data[mvid] = chartnew.data[mvid]
            status = 5

        elif len(chartnew.data[mvid]) == 1 \
             and len(chartold.data[mvid]) == 24: #Errorで取得された破損データ(Error)
            status = 4

        elif len(chartold.data[mvid]) in [48,49]: #Errorで取得された正常データ(Dual)
            status = 3
            chartunite.data[mvid] = screen(chartold.data[mvid], chartnew.data[mvid])

        elif chartnew.data[mvid] == chartold.data[mvid]: #Error時に取得限界より遠かった(Oldest)
            chartunite.data[mvid] = chartnew.data[mvid]
            status = 1

        else:
            print(mvid , 'is unexpected error pattern.')

        counter[status] += 1

    for mvid in chartold.data.keys():
        if mvid not in chartnew.data: #Legacy
            counter[0] += 1

    print(len(chartnew.data))
    print(len(chartold.data))
    for x in zip(name,counter):
        print(x)
    chartunite.write()

def main(initialize = False):
    unite()

if __name__ == '__main__':
    main(initialize = True)
