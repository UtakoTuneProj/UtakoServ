# -*- coding: utf-8 -*-
# SQL core module
import os
import random
import configparser

import MySQLdb
import sqlalchemy as alch
import sqlalchemy.sql as alchsql
import sqlalchemy.exc as alchexc
from sqlalchemy.orm.session import sessionmaker

import commondef as cmdf

from loginit import *
logger = getLogger(__name__)

cnfp = configparser.ConfigParser()
cnfp.read('conf/auth.conf')

engine = alch.engine_from_config(cnfp['alch'], prefix = 'alch.')
connection = engine.connect()
session = sessionmaker(bind = connection)()
metadata = alch.MetaData(bind = connection, reflect = True)
tables = metadata.tables

def fetch(isTrain = False, mvid = None):
    if mvid == None and not isTrain:
        raise ValueError('Neither mvid nor isTrain was given.')

    shapedInputs = []
    shapedOutputs = []

    rawCharts = []
    if isTrain:

        print("Fetching from database...")
        for i in range(20):
            rawCharts.append(
                connection.execute(
                    alchsql.select([
                        tables['chart']
                    ]).select_from(
                        tables['chart'].join(
                            tables['status'],
                            tables['status'].c.ID ==
                            tables['chart'].c.ID
                        )
                    ).where(
                        alchsql.and_(
                            tables['status'].c.analyzeGroup == i,
                            tables['status'].c.isComplete == 1
                    )).order_by(
                        tables['chart'].c.ID,
                        tables['chart'].c.epoch
            )).fetchall())
        print("Fetch completed. Got data size is "\
            + str(sum([len(rawCharts[i]) for i in range(20)])))

    else:
        rawCharts.append(
            connection.execute(
                alchsql.select([
                    tables['chart']
                ]).where(
                    tables['chart'].c.ID == mvid
                ).order_by(
                    tables['chart'].c.epoch
        )).fetchall())

        if len(rawCharts[0]) < 24:
            raise ValueError(mvid + ' is not analyzable')

    mvid = None

    for rawGroup in rawCharts:
        shapedInputs.append([])
        shapedOutputs.append([])
        for cell in rawGroup:
            if mvid != cell[0]:
                shapedInputs[-1].append([])
                mvid = cell[0]

            if cell[1] != 24:
                shapedInputs[-1][-1].extend(cell[3:])
            elif isTrain:
                view = cell[3]
                comment = cell[4]
                mylist = cell[5]

                cm_cor = (view + mylist) / (view + comment + mylist)
                shapedOutputs[-1].append(
                    [view + comment * cm_cor + mylist ** 2 / view * 2]
                )

    return [shapedInputs, shapedOutputs]

def fetchTag(isTrain = False, tagName = None):
    if tagName == None and not isTrain:
        raise ValueError('Neither tagName nor isTrain was given.')

    shapedInputs = []
    shapedOutputs = []

    rawCharts = []
    if isTrain:

        print("Fetching from database...")
        for i in range(20):
            rawCharts.append(
                alchsql.select([
                    tables['IDtag'].c.tagName,
                    alchsql.func.count(),
                    alchsql.func.avg(
                        tables['chart'].c.View
                    ),alchsql.func.avg(
                        tables['chart'].c.Comment
                    ),alchsql.func.avg(
                        tables['chart'].c.MyList
                    ),alchsql.func.max(
                        tables['chart'].c.View
                    ),alchsql.func.max(
                        tables['chart'].c.Comment
                    ),alchsql.func.max(
                        tables['chart'].c.MyList
                    )
                ]).select_from(
                    tables['chart'].join(
                        tables['status'].join(
                            tables['IDtag'],
                            tables['IDtag'].c.ID == tables['status'].c.ID
                        ),
                        tables['chart'].c.ID == tables['status'].c.ID
                )).where(
                    tables['chart'].c.epoch == 24
                ).group_by(
                    tables['IDtag'].c.tagName
                ).execute().fetchall()
            )
        print("Fetch completed. Got data size is "\
            + str(sum([len(rawCharts[i]) for i in range(20)])))

    else:
        rawCharts.append(
            alchsql.select([
                tables['IDtag'].c.tagName,
                alchsql.func.count(),
                alchsql.func.avg(
                    tables['chart'].c.View
                ),alchsql.func.avg(
                    tables['chart'].c.Comment
                ),alchsql.func.avg(
                    tables['chart'].c.MyList
                ),alchsql.func.max(
                    tables['chart'].c.View
                ),alchsql.func.max(
                    tables['chart'].c.Comment
                ),alchsql.func.max(
                    tables['chart'].c.MyList
                )
            ]).select_from(
                tables['chart'].join(
                    tables['status'].join(
                        tables['IDtag'],
                        tables['IDtag'].c.ID == tables['status'].c.ID
                    ),
                    tables['chart'].c.ID == tables['status'].c.ID
            )).where(
                tables['chart'].c.epoch == 24
            ).group_by(
                tables['IDtag'].c.tagName
            ).execute().fetchall()
        )

        if len(rawCharts[0]) == 0:
            raise ValueError(tagName + ' is not analyzable')

    tagName = None

    for rawGroup in rawCharts:
        shapedInputs.append([])
        shapedOutputs.append([])
        for cell in rawGroup:
            if tagName != cell[0]:
                shapedInputs[-1].append([])
                tagName = cell[0]

            if cell[1] != 24:
                shapedInputs[-1][-1].extend(cell[3:])
            elif isTrain:
                view = cell[3]
                comment = cell[4]
                mylist = cell[5]

                cm_cor = (view + mylist) / (view + comment + mylist)
                shapedOutputs[-1].append(
                    [view + comment * cm_cor + mylist ** 2 / view * 2]
                )

    return [shapedInputs, shapedOutputs]
