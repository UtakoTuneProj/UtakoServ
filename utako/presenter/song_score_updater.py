#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from peewee import fn

from utako.model.abstract_model import database
from utako.model.chart import Chart
from utako.model.status import Status
from utako.model.song_index import SongIndex
from utako.model.analyze_queue import AnalyzeQueue
from utako.presenter.xml_reader import XmlReader
from utako.exception.mov_deleted_exception import MovDeletedException
from utako.exception.no_response_exception import NoResponseException

BACKWARD_VIEW_WEIGHT = np.array((0.68, 0.16, 0.017, -0.15, 0.69))
BACKWARD_COMMENT_WEIGHT = np.array((-0.066, 0.86, 0.064, -0.041, 0.19))
BACKWARD_MYLIST_WEIGHT = np.array((-0.04, 0.14, 0.8, -0.03, 0.14))

FORWARD_VIEW_WEIGHT = np.array((0.90, 0.028, 0.19, -0.41, 1.62))
FORWARD_COMMENT_WEIGHT = np.array((0.20, 0.83, 0.068, -0.28, 0.70))
FORWARD_MYLIST_WEIGHT = np.array((0.18, 0.022, 0.95, -0.26, 0.64))

class SongScoreUpdater:
    def __call__(self, mvid):
        '''
        SongScoreUpdater(mvid):
        Updates status.score of target song
        Args: mvid(str): nico id for target movie
        Returns: status(StatusRecord): target status record
        '''

        chart = Chart.select(
            Chart.view,
            Chart.comment,
            Chart.mylist
        ).where(
            Chart.status_id == mvid,
            10140 < Chart.time,
            Chart.time < 10260,
        ).first()
        if len(chart) == 0: #if collect chart does not exist
            try:
                ret = XmlReader()(mvid)
            except MovDeletedException: #if deleted
                return Status.update({
                    Status.score: None,
                    Status.score_status: -2
                }).where(
                    Status.id == mvid
                )
                
            days = (datetime.datetime.now() - ret["first_retrieve"]).days
            if days >= 7: #Backward Predict
                predict_args = np.array((
                    ret['view_counter'] + 1,
                    ret['comment_num'] + 1,
                    ret['mylist_counter'] + 1,
                    days,
                    10
                ))
                view = ( predict_args ** BACKWARD_VIEW_WEIGHT ).prod()
                comment = ( predict_args ** BACKWARD_COMMENT_WEIGHT ).prod()
                mylist = ( predict_args ** BACKWARD_MYLIST_WEIGHT ).prod()
                score_status = -1

            else: #Forward Predict
                minutes = (datetime.datetime.now() - ret["first_retrieve"]).total_seconds() / 60
                predict_args = np.array((
                    ret['view_counter'] + 1,
                    ret['comment_num'] + 1,
                    ret['mylist_counter'] + 1,
                    minutes + 1,
                    10
                ))
                view = ( predict_args ** FORWARD_VIEW_WEIGHT ).prod()
                comment = ( predict_args ** FORWARD_COMMENT_WEIGHT ).prod()
                mylist = ( predict_args ** FORWARD_MYLIST_WEIGHT ).prod()
                score_status = 1

        else:
            view = chart.view
            comment = chart.comment
            mylist = chart.mylist
            score_status = 0

        score = np.sqrt(view) * (1 - 0.5 * 10**(-20 * comment / view)) * (1 - 0.5 * 10**(-20 * mylist / view))
        return Status.update({
            Status.score: score,
            Status.score_status: score_status
        }).where(
            Status.id == mvid
        )

    def update(self, *status_ids):
        '''
        SongScoreUpdater.update(*status_ids)
        batch update scores for specified ids
        and throw it into AnalyzeQueue if conditions are satisfied.

        In: *status_ids: target id(s)
        '''
        queries = []
        pg = ProgressBar()
        for status_id in pg( status_ids ):
            queries.append(self(status_id))

        with database.atomic():
            for query in queries:
                if query is not None:
                    query.execute()

        analyze_queue = Status.select(Status.id).where(
            ( Status.score > settings['analyze_score_limit'] )
            & ( Status.id.in_(status_ids) )
            & ( Status.id.not_in(
                SongIndex.select(SongIndex.status_id)).where(SongIndex.version == settings['model_version']) 
            )
        )

        AnalyzeQueue.insert_many(
            [{
                'movie_id': m.id,
                'version': settings['model_version'],
                'status': 0,
            } for m in analyze_queue]
        ).execute()
