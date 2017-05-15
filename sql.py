# coding: utf-8
# SQL core module
import os
import random
import configparser
import MySQLdb
import commondef as cmdf

cnfp = configparser.ConfigParser()
cnfp.read('.auth.conf')

connection = MySQLdb.connect(**cnfp['DEFAULT'])
cursor = connection.cursor()

class Table:
    def __init__(self, name, db):
        self.name = name
        self.cursor = db.cursor
        self.parent = db
        db.setTable(self)

        self.primaryKey = []
        self.columns = []
        self.cursor.execute('desc `{}`'.format(name))
        for column in self.cursor.fetchall():
            if 'PRI' in column[3]:
                self.primaryKey.append(column[0])
            else:
                self.columns.append(column[0])
        self.allcolumns = self.primaryKey + self.columns

    def primaryQuery(self, *unnamed, **named):
        i = 0
        q = (
            "`{}` = %s AND " * (len(self.primaryKey)) - 1 * "`{}` = %s"
        ).format(*self.primaryKey)
        args = []

        for pk in self.primaryKey:
            if pk in named:
                args.append(named[key])
            else:
                args.append(unnamed[i])
                i += 1

        return connection.literal(q, args)

    def get(self, query, args):
        self.cursor.execute(
            'SELECT * from `{0}` where {1}'.format(self.name, query),
            (args,)
        )
        return self.cursor.fetchall()

    def primaryGet(self, *unnamed, **named):
        return self.get(self.primaryQuery(*unnamed, **named))

    def set(self, *unnamed, overwrite = True, **named):
        i = 0

        ql = []

        for key in self.primaryKey:
            if key in named:
                tmp = named[key]
            else:
                tmp = unnamed[i]
                i += 1
            ql.append(connection.literal(tmp))

        for key in self.columns:

            if key in named:
                tmp = named[key]
            else:
                tmp = unnamed[i]
                i += 1

            if tmp == None:
                tmp = 'NULL'
            elif not key == 'postdate':
                tmp = connection.literal(tmp)

            ql.append(tmp)

        q = (
            '( ' + '{}, ' * (len(self.allcolumns) - 1) + '{} )'
        ).format(*ql)
        dupq = (
            '`{0[0]}` = {0[1]} ' * len(self.columns)
        ).format(*zip(self.columns, ql[len(self.primaryKey):]))
        cmd = \
            'INSERT into {} \n'.format(self.name) + \
            'values ' + q + '\n'\
            'ON DUPLICATE key update ' + dupq
        self.cursor.execute(cmd)

class ChartTable(Table):
    def __init__(self, database):
        super().__init__(
            'chart',
            database
        )

    def update(self):
        #statusDBを読みチャートを更新

        qtbl = self.parent.table['status']
        ittbl = self.parent.table['IDtag']
        todays_mv \
            = qtbl.get(
                "adddate(postdate, interval '1 0' day_hour)" + \
                " > current_timestamp()" + \
                " and (validity = 1)",
                (),
            )
        lastwks_mv \
            = qtbl.get(
                "adddate(postdate, interval '7 1' day_hour)" + \
                " < current_timestamp()" + \
                " and (validity = 1) and (isComplete = 0)",
                (),
            )

        for query in todays_mv + lastwks_mv:
            mvid = query[0]
            epoch = query[2]
            postdate = query[4]
            try:
                movf = cmdf.MovInfo(mvid)
                movf.update()

            except cmdf.MovDeletedException:
                qtbl.set(
                    mvid,
                    0,
                    *query[2:4],
                    "convert('" + str(postdate) + "', datetime)",
                    None
                    )
                continue

            except cmdf.NoResponseException:
                while True:
                    time.wait(5)
                    movf.update()

            passedmin = (cmdf.now.dt - movf.first_retrieve.dt).total_seconds() / 60
            writequery = {
                "ID":       mvid,
                "epoch":    epoch,
                "Time":     passedmin,
                "View":     movf.view_counter,
                "Comment":  movf.comment_num,
                "Mylist":   movf.mylist_counter
            }
            self.set(**writequery)

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
                    writequery = {
                        "ID"      : mvid,
                        "tagName" : tag,
                        "count"   : 1,
                    }
                    ittbl.set(**writequery)
                isComplete = True

            writequery = {
                "ID":           mvid,
                "validity":     1 if status else 0,
                "epoch":        epoch + 1,
                "isComplete":   1 if isComplete else 0,
                "postdate":     "convert('" + str(postdate) + "', datetime)",
                "analyzeGroup": random.randint(0,19) if isComplete else None
            }
            qtbl.set(**writequery)

        return None

class QueueTable(Table):
    def __init__(self, database):
        super().__init__(
            'status',
            database
        )

    def update(self): #ランキング取得・キュー生成部

        for i in range(15): #15ページ目まで取得する
            cmdf.rankfilereq(page = i)
            raw_rank = cmdf.JSONfile("ranking/" + str(i) + ".json").data['data']
            for mvdata in raw_rank:
                mvid = mvdata['contentId']
                postdate = cmdf.Time('n', mvdata['startTime'])
                if len(self.primaryGet(ID = mvid)) == 0:
                    #取得済みリストの中に含まれていないならば
                    self.set(
                        ID          = mvid,
                        validity    = 1,
                        epoch       = 0,
                        isComplete  = 0,
                        postdate    = "convert('" + str(postdate.dt) + \
                                        "', datetime)",
                        analyzeGroup= None
                    )
                else:
                    break
            else:
                continue
            break

        for j in range(i+1):
            os.remove("ranking/" + str(j) + ".json")

        return None

class IDTagTable(Table):
    def __init__(self, database):
        super().__init__(
            'IDtag',
            database,
        )

class DataBase:
    def __init__(self, name, connection = connection):
        self.name = name
        self.connection = connection
        self.cursor = connection.cursor()
        self.table = {}

    def commit(self):
        self.connection.commit()

    def get(self, query, args):
        self.cursor.execute(query, args,)
        return self.cursor.fetchall()

    def setTable(self, table):
        self.table[table.name] = table
