#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SQL core module
from common_import import *

import commondef as cmdf

cnfp = configparser.ConfigParser()
cnfp.read('.auth.conf')

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
                ).execute().fetchall()
            )
        print("Fetch completed. Got data size is "\
            + str(sum([len(rawCharts[i]) for i in range(20)])))

    else:
        rawCharts.append(
            alchsql.select([
                tables['chart']
            ]).where(
                tables['chart'].c.ID == mvid
            ).order_by(
                tables['chart'].c.epoch
            ).execute().fetchall()
        )

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
