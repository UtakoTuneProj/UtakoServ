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
        self.cursor.execute("desc " + name)
        for column in self.cursor.fetchall():
            if 'PRI' in column[3]:
                self.primaryKey.append(column[0])
            else:
                self.columns.append(column[0])
        self.allcolumns = self.primaryKey + self.columns

    def primaryQuery(self, *unnamed, **named):
        i = 0
        q = ""
        for pk in self.primaryKey:
            if pk in named:
                q += pk + " = '" + str(named[pk]) + "' AND "
            else:
                q += pk + " = '" + str(unnamed[i]) + "' AND "
                i += 1

        return q.rpartition(" AND ")[0]

    def get(self, query):
        self.cursor.execute('SELECT * from ' + self.name + ' where ' + query)
        return self.cursor.fetchall()

    def primaryGet(self, *unnamed, **named):
        return self.get(self.primaryQuery(*unnamed, **named))

    def set(self, *unnamed, overwrite = True, **named):
        i = 0

        q = '('
        dupq = ''
        for key in self.primaryKey:
            if key in named:
                tmp = named[key]
            else:
                tmp = unnamed[i]
                i += 1
            q += "'" + str(tmp) + "',"

        for key in self.columns:

            if key in named:
                tmp = named[key]
            else:
                tmp = unnamed[i]
                i += 1

            if not (key == 'postdate' or tmp == None):
                q += "'"

            if tmp == None:
                q += "NULL"
                dupq += key + "=NULL, "

            else:
                q += str(tmp)
                dupq += key + "=" + str(tmp) + ", "

            if key == 'postdate' or tmp == None:
                q += ", "
            else:
                q += "', "

        q = q[:-2]
        q += ')'
        dupq = dupq[:-2]

        cmd = \
            'INSERT into ' + self.name + ' values ' + q + ' ' + \
            'ON DUPLICATE key update ' + dupq
        self.cursor.execute(cmd)

class ChartTable(Table):
    def __init__(self, database):
        super().__init__(
            'chart',
            database
        )
        self.qtbl = self.parent.table['status']

    def update(self):
        #statusDBを読みチャートを更新

        todays_mv \
            = self.qtbl.get(
                "adddate(postdate, interval '1 0' day_hour)" + \
                " > current_timestamp()" + \
                " and (validity = 1)"
            )
        lastwks_mv \
            = self.qtbl.get(
                "adddate(postdate, interval '7 1' day_hour)" + \
                " < current_timestamp()" + \
                " and (validity = 1) and (isComplete = 0)"
            )

        for query in todays_mv + lastwks_mv:
            mvid = query[0]
            epoch = query[2]
            postdate = query[4]
            try:
                movf = cmdf.MovInfo(mvid)
                movf.update()

            except cmdf.MovDeletedException:
                self.qtbl.set(
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
                isComplete = True

            writequery = {
                "ID":           mvid,
                "validity":     1 if status else 0,
                "epoch":        epoch + 1,
                "isComplete":   1 if isComplete else 0,
                "postdate":     "convert('" + str(postdate) + "', datetime)",
                "analyzeGroup": random.randint(0,19) if isComplete else None
            }
            self.qtbl.set(**writequery)

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

class DataBase:
    def __init__(self, name, connection = connection):
        self.name = name
        self.connection = connection
        self.cursor = connection.cursor()
        self.table = {}

    def commit(self):
        self.connection.commit()

    def get(self, query):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def setTable(self, table):
        self.table[table.name] = table
