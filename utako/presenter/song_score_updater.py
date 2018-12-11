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
            if days >= 7:
                predict = lambda x, a, b: x * ( a * np.log10(days) + b)
                view = predict(ret['view_counter'], 0.11, 0.93)
                comment = predict(ret['comment_num'], 0.05, 0.97)
                mylist = predict(ret['mylist_counter'], 0.03, 0.98)
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
