# coding: utf-8
# ServCore: core module for hourly task

import Analyzer as analyzer
sql = analyzer.sql
cmdf = analyzer.cmdf
from tweepyCore import chart_tw

def main():
    db    = sql.DataBase("tesuto", sql.connection)
    qtbl  = sql.QueueTable(db)
    ctbl  = sql.ChartTable(db)
    ittbl = sql.IDTagTable(db)

    qtbl.update()
    ctbl.update()

    # qf.tweet(24, 300)
    db.commit()

    return 0

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='UTF-8')
if __name__ == '__main__':
    main()
