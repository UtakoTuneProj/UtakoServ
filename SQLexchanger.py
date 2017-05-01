#!/usr/bin/env python3
#convert Chartfile into SQL
import time
from progressbar import ProgressBar

import UtakoChartInitializer
import ServCore as core

if __name__ == '__main__':
    cf = core.Chartfile()
    dat = cf.read()
    p = ProgressBar(0, len(dat))

    db = core.DataBase()
    ctbl = core.ChartTable(db)
    qtbl = core.QueueTable(db)

    print('Migrating UtakoFiles...')
    for i, mvid in enumerate(dat):
        p.update(i+1)
        status = True
        completed = False

        try:
            mvinfo = core.MovInfo(mvid)
        except MovDeletedException:
            continue
        except NoResponseException:
            while True:
                time.sleep(5)
                mvinfo = core.MovInfo(mvid)

        startTime = core.time('n', mvinfo.first_retrieve)

        for j, cell in enumerate(dat[mvid]):
            ctbl.set([mvid, j,] + cell)

            if j < 24:
                if cell[0] < j*60 or ((j+1)*60 + 30 < cell[0]):
                    status = False
            elif j > 24:
                status = False
            elif cell[0] < 10140 or 10200 + 30 < cell[0]:
                status = False

        if status and len(dat[mvid]) == 25:
            completed = True

        qtbl.set([
            mvid,
            status,
            len(dat),
            completed,
            "convert('" + str(startTime) + "')"
        ])

    db.commit()
