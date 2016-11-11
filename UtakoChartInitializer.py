# coding: utf-8
import codecs
import json
import datetime

import UtakoServCore as core

class TagStatFile(core.JSONfile):
    #TagStatFile:[[tagname, last_search, hits],...]
    def __init__(self, path = 'dat/tagstat.json'):
        super().__init__(path = path)

    @property
    def data():
        return self._data

    @data.setter
    def data():
        self.tags = list(zip(*self.data))[0]
        self.valid = map(lambda x:core.Time(x, mode = 's'), list(zip(*self.data))[1] )
        self.hits = map(int, list(zip(*self.data))[2] )

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
        except core.NoResponseException:
            print('No response for ' + mvid + '.', flush = True)
            continue
        chart = chartf.data[mvid]
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
                    if tagstatf.valid[x].dt < now.dt:
                        core.rankfilereq(searchtag = tag)
                        rankf = core.JSONfile('ranking/0.json')
                        tagstatf.data[x] = [
                                            tag,
                                            Time( now.dt
                                                + datetime.timedelta(weeks = 1),
                                                  mode = 'dt').str12,
                                            rankf.data['meta']['totalcount']
                                           ]
                else:
                    x = -1
                    core.rankfilereq(searchtag = tag)
                    rankf = core.JSONfile('ranking/0.json')
                    tagstatf.data.append([
                                          tag,
                                          Time( now.dt
                                              + datetime.timedelta(weeks = 1),
                                                mode = 'dt').str12,
                                          rankf.data['meta']['totalCount']
                                         ])
                tagstat.append(tagstatf.hits[x])
                if len(tagstat) > 11:
                    tagstat = tagstat[0:11]
                elif len(tagstat) < 11:
                    tagstat.extend([0 for i in range(11 - len(tagstat))])
            chart.insert(-1, [
                              thumb.first_retrieve.dt.hour,
                              thumb.first_retrieve.dt.weekday()
                             ].extend(tagstat))
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
