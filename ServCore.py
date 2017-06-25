#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# ServCore: core module for hourly task

import datetime

import Analyzer as analyzer
sql = analyzer.sql
cmdf = analyzer.cmdf
from tweepyCore import chart_tw

from loginit import *
logger = getLogger('progress')

def main():
    db    = sql.DataBase("utakodb", sql.connection)
    qtbl  = sql.QueueTable(db)
    ctbl  = sql.ChartTable(db)
    ittbl = sql.IDTagTable(db)

    qtbl.update()
    ctbl.update()

    # qf.tweet(24, 300)
    db.commit()

    return None

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='UTF-8')
if __name__ == '__main__':
    startTime = datetime.datetime.now()
    logger.info('Utako Task Started at {}'.format(startTime))

    try:
        main()
    except Exception as e:
        logger.error(e)
    else:
        endTime = datetime.datetime.now()
        logger.info(
            'Utako Task successfully finished. Exec Time: {}'
            .format(endTime - startTime)
        )
