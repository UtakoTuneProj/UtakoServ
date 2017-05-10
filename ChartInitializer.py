# coding: utf-8
# ChartInitializer: makes formatted chart file from completed queues

import codecs
import json
import datetime
import math as m
import os
import binascii

import ServCore as core

class TagStatFile(core.JSONfile):
    #TagStatFile:[[tagname, valid, hits],...]
    def __init__(self, path = 'dat/tagstat.json'):
        super().__init__(path = path)
        self.saved = True

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data
        self.tags = list(zip(*data))[0]
        self.valid = list(map(lambda x:core.Time(stream = str(x), mode = 's'), list(zip(*data))[1] ))
        self.hits = list(map(int, list(zip(*data))[2] ))
        self.saved = False

    def update(self, tag):
        if tag in self.tags:
            x = self.tags.index(tag)
            if self.valid[x].dt > core.now.dt:
                return x
        else:
            x = len(self.data)
            self.data.append(None)
        core.rankfilereq(searchtag = tag)
        hits = core.JSONfile('ranking/0.json').data['meta']['totalCount']
        self.data[x] = [
            tag,
            core.Time( stream =
                core.now.dt
              + datetime.timedelta(days = 7 + 3 * m.log10(hits+1)),
                mode = 'dt'
            ).str12,
            hits
        ]
        os.remove('ranking/0.json')
        return x

def normalizer(mvid, on_prog = False):
    #get chart from chartfile, and convert to Analyzer-readable format
    #if on_prog == True then return value if on progress,
    # else only returns status only
    #return value:[
    #     Status('deleted', 'no_response', 'completed', 'broken', range(1,25)),
    #     x, (input data)
    #     y  (output teacher data)
    # ]

    chartf = core.Chartfile()
    tagstatf = TagStatFile()

    try:
        thumb = core.MovInfo(mvid)
    except core.MovDeletedException:
        print(mvid + ' has been deleted.')
        return ['deleted', None, None]
    except core.NoResponseException:
        print('No response for '+ mvid)
        return ['no_response', None, None]

    #http://qiita.com/utgwkk/items/5ad2527f19150ae33322
    chart = chartf.data[mvid][:]
    status = True
    for i,cell in enumerate(chart):
        if i < 24:
            if cell[0] < i*60 or ((i+1)*60 + 30 < cell[0]):
                status = False
                break
        elif i > 24:
            status = False
            break
        elif cell[0] < 10140 or 10200 + 30 < cell[0]:
            status = False
            break

    if status and not on_prog and len(chart) != 25:
        status = len(chart)
        x = None
        y = None
    elif status:
        x = []
        tagstat = []
        for cell in chart:
            x.extend(cell)
        if len(chart) == 25:
            y = x[-4:]
            x = x[:-4]
            status = 'completed'
        else:
            y = None
            status = len(chart)
        for tag in thumb.tags:
            i = tagstatf.update(tag)
            if tagstatf.data[i][2] >= 50:
                tagstat.append(i)
            # tagstat.append(binascii.crc32(tagstatf.data[i][0].encode('utf-8')) & 0xffffff)
        # tagstat.sort()
        # tagstat.reverse()
        if len(tagstat) > 11:
            tagstat = tagstat[0:11]
        elif len(tagstat) < 11:
            tagstat.extend([0 for i in range(11 - len(tagstat))])
        x.extend([thumb.first_retrieve.dt.hour, thumb.first_retrieve.dt.weekday()])
        x.extend(tagstat)
    else:
        status = 'broken'
        x = None
        y = None

    if not tagstatf.saved:
        tagstatf.write()

    return [status, x, y]

def main(initialize = False):

    chartf = core.Chartfile()
    initf  = core.InitChartfile()
    queuef = core.Queuefile()

    if initialize:
        initf.data = []
    crushedList = []

    for mvid in chartf.data.keys():
        if mvid in initf.mvid:
            continue
        [status, x, y] = normalizer(mvid)
        if status in ['broken', 'deleted']:
            crushedList.append(mvid)
        elif status == 'completed':
            initf.data.append([mvid,x,y])

    for mvid in crushedList:
        del chartf.data[mvid]
    print('len(chartf.data) :', len(chartf.data))
    print('len(initf.data)  :', len(initf.data))

    chartf.write()
    initf.write()

if __name__ == '__main__':
    main(initialize = False)
