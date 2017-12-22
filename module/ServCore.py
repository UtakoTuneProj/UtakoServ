#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ServCore: core module for hourly task

from common_import import *

import Analyzer as analyzer
sql = analyzer.sql
cmdf = analyzer.cmdf
from tweepyCore import chart_tw

from presenter.json_reader import JsonReader

def qtblUpdate(): #ランキング取得・キュー生成部

    for i in range(15): #15ページ目まで取得する
        cmdf.rankfilereq(page = i)
        raw_rank = JsonReader()("ranking/" + str(i) + ".json")['data']
        for mvdata in raw_rank:
            mvid = mvdata['contentId']
            postdate = cmdf.Time('n', mvdata['startTime'])
            if len(sql.tables['status'].select().where(
                sql.tables['status'].c.ID == mvid
            ).execute().fetchall()) == 0:
            
                #取得済みリストの中に含まれていないならば
                sql.tables['status'].insert().values(
                    ID          = mvid,
                    validity    = 1,
                    epoch       = 0,
                    isComplete  = 0,
                    postdate    = postdate.dt,
                    analyzeGroup= None
                ).execute()
            else:
                break
        else:
            continue
        break

    for j in range(i+1):
        os.remove("ranking/" + str(j) + ".json")

    return None

def ctblUpdate():
    #statusDBを読みチャートを更新

    todays_mv \
        = sql.connection.execute(
            sql.tables['status'].select().where(
                sql.alchsql.and_(
                    sql.tables['status'].c.postdate
                    > cmdf.Time().dt - datetime.timedelta(days = 1),
                    sql.tables['status'].c.validity == 1
    ))).fetchall()
    lastwks_mv \
        = sql.connection.execute(
            sql.tables['status'].select().where(
                sql.alchsql.and_(
                    sql.tables['status'].c.postdate
                    < cmdf.Time().dt - datetime.timedelta(days=7, hours=1),
                    sql.tables['status'].c.validity == 1,
                    sql.tables['status'].c.isComplete == 0
    ))).fetchall()

    for query in todays_mv + lastwks_mv:
        mvid = query[0]
        epoch = query[2]
        postdate = query[4]
        try:
            movf = cmdf.MovInfo(mvid)
            movf.update()

        except cmdf.MovDeletedException:
            sql.tables['status'].update(
            ).where(
                sql.tables['status'].c.ID == mvid
            ).values(
                validity = False
            ).execute()
            continue

        except cmdf.NoResponseException:
            while True:
                time.wait(5)
                movf.update()

        passedmin = (cmdf.now.dt - movf.first_retrieve.dt).total_seconds() / 60

        try:
            sql.tables['chart'].insert().values(
                ID = mvid,
                epoch = epoch,
                Time = passedmin,
                View = movf.view_counter,
                Comment = movf.comment_num,
                Mylist = movf.mylist_counter
            ).execute()
        except sql.alchexc.IntegrityError:
            pass

        isComplete = False
        status = True

        if epoch < 24:
            if passedmin < epoch*60 or ((epoch+1)*60 + 30 < passedmin):
                status = False
        elif epoch > 24:
            status = False
        elif passedmin < 10140 or 10200 + 30 < passedmin:
            status = False

        if status and epoch == 24:
            for tag in movf.tags:
                try:
                    sql.tables['IDtag'].insert().values(
                        ID = mvid,
                        tagName = tag,
                        count = 1
                    )
                except sql.alchexc.IntegrityError:
                    pass
            isComplete = True

        sql.tables['status'].update().where(
            sql.tables['status'].c.ID == mvid
        ).values(
            validity = status,
            epoch = epoch + 1,
            isComplete = isComplete,
            analyzeGroup = random.randint(0,19) if isComplete else None
        ).execute()

    return None

def main():
    try:
        qtblUpdate()
        ctblUpdate()

        # qf.tweet(24, 300)
    finally:
        sql.session.commit()

    return 0

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='UTF-8')
if __name__ == '__main__':
    main()
