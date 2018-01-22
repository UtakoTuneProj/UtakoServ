#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utako.common_import import *

from utako.model.chart import Chart
from utako.model.status import Status
from utako.model.idtag import Idtag

class ChartFetcher:
    def __call__(self, isTrain = False, mvid = None):
        if mvid == None and not isTrain:
            raise ValueError('Neither mvid nor isTrain was given.')

        shapedInputs = []
        shapedOutputs = []

        rawCharts = []
        if isTrain:
            charts = Chart.select().join(
                Status,
                on = (Status.id == Chart.id)
            ).where(
                Status.iscomplete == 1
            ).order_by(
                Chart.id,
                Chart.epoch
            )
            for i in range(20):
                rawCharts.append(
                    charts.where(
                        Status.analyzegroup == i
                    ).dicts()
                )

        else:
            rawCharts.append(
                Chart.select()
                .where(
                    Status.id == mvid
                ).order_by(
                    Chart.epoch
                ).dicts()
            )

            if len(rawCharts[0]) < 24:
                raise ValueError(mvid + ' is not analyzable')

        mvid = None

        for rawGroup in rawCharts:
            shapedInputs.append([])
            shapedOutputs.append([])
            for cell in rawGroup:
                if mvid != cell['id']:
                    shapedInputs[-1].append([])
                    mvid = cell['id']

                if cell['epoch'] != 24:
                    for item in ('view', 'comment', 'mylist'):
                        shapedInputs[-1][-1].append(cell[item])
                elif isTrain:
                    view = cell['view']
                    comment = cell['comment']
                    mylist = cell['mylist']

                    cm_cor = (view + mylist) / (view + comment + mylist)
                    shapedOutputs[-1].append(
                        [view + comment * cm_cor + mylist ** 2 / view * 2]
                    )

        return [shapedInputs, shapedOutputs]
