# coding: utf-8
import codecs
import json
import datetime
import math as m

import UtakoServCore as core

class TagStatFile(core.JSONfile):
    #TagStatFile:[[tagname, valid, hits],...]
    def __init__(self, path = 'dat/tagstat.json'):
        super().__init__(path = path)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data
        self.tags = list(zip(*data))[0]
        self.valid = list(map(lambda x:core.Time(stream = str(x), mode = 's'), list(zip(*data))[1] ))
        self.hits = list(map(int, list(zip(*data))[2] ))

def main(initialize = False):

    chartf = core.Chartfile()
    initf = core.JSONfile('dat/chartlist_init.json')
    tagstatf = TagStatFile()

    if initialize:
        initf.data = []
    crushedList = []

    for mvid in chartf.data.keys():
        try:
            thumb = core.MovInfo(mvid)
        except core.MovDeletedException:
            status = False
            print(mvid + ' has been deleted.', flush = True)
            crushedList.append(mvid)
            continue
        except core.NoResponseException:
            print('No response for ' + mvid + '.', flush = True)
            continue

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
        if status and (chart not in initf.data) and (len(chart) == 25):
            tagstat = []
            for tag in thumb.tags:
                if tag in tagstatf.tags:
                    x = tagstatf.tags.index(tag)
                    if tagstatf.valid[x].dt < core.now.dt:
                        core.rankfilereq(searchtag = tag)
                        hits = core.JSONfile('ranking/0.json').data['meta']['totalCount']
                        tagstatf.data[x] = [
                                            tag,
                                            core.Time( stream =  core.now.dt
                                                     + datetime.timedelta(days = 7 + 3 * m.log10(hits+1)),
                                                       mode = 'dt').str12,
                                            hits
                                           ]
                else:
                    x = -1
                    core.rankfilereq(searchtag = tag)
                    hits = core.JSONfile('ranking/0.json').data['meta']['totalCount']
                    tagstatf.data.append([
                                          tag,
                                          core.Time( stream =  core.now.dt
                                                   + datetime.timedelta(days = 7 + 3 * m.log10(hits+1)),
                                                     mode = 'dt').str12,
                                          hits
                                         ])
                tagstat.append(m.log10(tagstatf.hits[x] + 1))
            tagstat.sort()
            tagstat.reverse()
            if len(tagstat) > 11:
                tagstat = tagstat[0:11]
            elif len(tagstat) < 11:
                tagstat.extend([0 for i in range(11 - len(tagstat))])
            x = [thumb.first_retrieve.dt.hour, thumb.first_retrieve.dt.weekday()]
            x.extend(tagstat)
            chart.insert(-1, x)
            initf.data.append(chart)
        elif status:
            pass
        else:
            crushedList.append(mvid)
    for mvid in crushedList:
        del chartf.data[mvid]
    print(len(chartf.data))
    print(len(initf.data))

    chartf.write()
    initf.write()
    tagstatf.write()

if __name__ == '__main__':
    main(initialize = False)
