#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from peewee import fn

from utako.model.abstract_model import database
from utako.model.chart import Chart
from utako.model.status import Status
from utako.presenter.xml_reader import XmlReader
from utako.exception.mov_deleted_exception import MovDeletedException
from utako.exception.no_response_exception import NoResponseException

VIEW_WEIGHT = np.array((0.68, 0.16, 0.017, -0.15, 0.69))
COMMENT_WEIGHT = np.array((-0.066, 0.86, 0.064, -0.041, 0.19))
MYLIST_WEIGHT = np.array((-0.04, 0.14, 0.8, -0.03, 0.14))

class SongScoreUpdater:
    def __call__(self, mvid): #ランキング取得・キュー生成部
        chart = Chart.select(
            Chart.view,
            Chart.comment,
            Chart.mylist
        ).where(
            Chart.status_id == mvid,
            10140 < Chart.time,
            Chart.time < 10260,
        ).first()
        if chart is None:
            try:
                ret = XmlReader()(mvid)
            except MovDeletedException:
                return
            except NoResponseException:
                return
                
            days = (datetime.datetime.now() - ret["first_retrieve"]).days
            predict_args = np.array((
                ret['view_counter'],
                ret['comment_num'],
                ret['mylist_counter'],
                days,
                10
            ))
            if days >= 7:
                view = ( predict_args ** VIEW_WEIGHT ).prod()
                comment = ( predict_args ** COMMENT_WEIGHT ).prod()
                mylist = ( predict_args ** MYLIST_WEIGHT ).prod()
                score_status = -1

            else:
                return

        else:
            view = chart.view
            comment = chart.comment
            mylist = chart.mylist
            score_status = 0

        score = np.sqrt(view) * (1-10**(-50 * comment / view)) * (1-10**(-50 * mylist / view))
        return Status.update({
            Status.score: score,
            Status.score_status: score_status
        }).where(
            Status.id == mvid
        )

    def update(self, *status_ids):
        queries = []
        pg = ProgressBar()
        for status_id in pg( status_ids ):
            queries.append(self(status_id))

        with database.atomic():
            for query in queries:
                if query is not None:
                    query.execute()
