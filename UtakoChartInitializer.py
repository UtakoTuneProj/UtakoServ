# coding: utf-8
import codecs
import json

import UtakoServCore as core

def main(initialize = False):

    chartf = core.Chartfile()
    initf = core.JSONfile('dat/chartlist_init.json')

    if initialize:
        initf.data = []
    crushedList = []

    for mvid in chartf.data.keys():
        # try:
        #     thumb = core.MovInfo(mvid)
        # except core.MovDeletedException:
        #     status = False
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

if __name__ == '__main__':
    main(initialize = False)
