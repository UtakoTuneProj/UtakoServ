#!/usr/bin/env python3

import UtakoChartInitializer
import UtakoServCore as core
from progressbar import ProgressBar

if __name__ == '__main__':
    cf = core.Chartfile()
    dat = cf.read()
    p = ProgressBar(0, len(dat))

    db = core.DataBase()

    for i, mvid in enumerate(dat):
        p.update(i+1)
        for j, cell in enumerate(dat[mvid]):
            db.setChart(mvid, j, *cell)

    db.commit()
