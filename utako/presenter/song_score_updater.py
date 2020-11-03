#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Tuple, Union

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
from utako.delegator.song_analyze import SongAnalyzeSender

from utako import root_logger

BACKWARD_PREDICT_MATRIX = np.array((
    ( 0.68 , 0.16, 0.017, -0.15 , 0.69),
    (-0.066, 0.86, 0.064, -0.041, 0.19),
    (-0.04 , 0.14, 0.8  , -0.03 , 0.14),
))

FORWARD_PREDICT_MATRIX = np.array((
    (0.90, 0.028, 0.19 , -0.41, 1.62),
    (0.20, 0.83 , 0.068, -0.28, 0.70),
    (0.18, 0.022, 0.95 , -0.26, 0.64),
))

class SongScoreUpdater:
    logger = root_logger.getChild('presenter.song_score_updater')

    def __call__(self, mvid):
        '''
        SongScoreUpdater(mvid):
        Updates status.score of target song
        Args: mvid(str): nico id for target movie
        Returns: status(StatusRecord): target status record
        '''

        charts = self._fetch_target_records(([mvid]))

        if len(charts) == 0: #if collect chart does not exist
            ret = XmlReader()(mvid)
            score_seeds = {
                'status_id':            mvid,
                'movie_first_retrieve': ret['first_retrive'],
                'view':                 ret['view_counter'],
                'comment':              ret['comment_num'],
                'mylist':               ret['mylist_counter'],
            }

        else:
            record = charts[0]
            score_seeds = {
                'status_id':            record.status.id,
                'movie_first_retrieve': record.status.postdate,
                'view':                 record.view,
                'comment':              record.comment,
                'mylist':               record.mylist,
                'minutes':              record.time,
            }

        return Status.bulk_update([
            self._create_update_model(**score_seeds)
        ], fields=[Status.score, Status.score_status])

    def update(self, *status_ids, enqueue=True):
        '''
        SongScoreUpdater.update(*status_ids)
        batch update scores for specified ids
        and throw it into AnalyzeQueue if conditions are satisfied.

        In: *status_ids: target id(s)
        '''
        chart_records = self._fetch_target_records(status_ids)
        score_update_models = self._create_update_models(chart_records)
        with database.atomic():
            [ record.save() for record in score_update_models ]

        analyze_queue = Status.select(Status.id).where(
            ( Status.score > settings['analyze_score_limit'] )
            & ( Status.id.in_(status_ids) )
            & ( Status.id.not_in(
                SongIndex.select(SongIndex.status_id).where(SongIndex.version == settings['model_version'])
            ))
        )

        if enqueue:
            [ SongAnalyzeSender().send(movie_id=m.id) for m in analyze_queue ]

        result_map_func = lambda status_record: {
            'id':           status_record.id,
            'score':        status_record.score,
            'score_status': status_record.score_status
        }
        return tuple(map(result_map_func, score_update_models))

    def _fetch_target_records(self, status_ids):
        '''
        SongScoreUpdater._fetch_target_records(status_ids)

        In: status_ids: list[str]: target movie ids
        Out: Cursor: latest chart records for target movie ids
        '''
        newestChart = Chart
        newestChartStatus = newestChart.status
        latestTime = fn.MAX(newestChart.time)
        latestTimeAlias = latestTime.alias('max_time')

        subquery = newestChart.select(
            newestChartStatus,
            latestTimeAlias,
        ).group_by(
            newestChart.status
        ).where(
            newestChart.status.in_(status_ids)
        )

        queries = Chart.select(
            Chart.id,
            Chart.status,
            Chart.view,
            Chart.comment,
            Chart.mylist,
            Chart.time,
        ).join(
            subquery,
            on=(Chart.status == newestChartStatus)
        ).where(
            Chart.time == latestTimeAlias
        )

        return queries.execute()

    def _create_update_models(self, chart_records):
        '''
        In: chart_records: list[Chart]: latest chart records used to update status scores
        Out: list[UpdateQuery]
        '''
        self.logger.info('Number of chart_records = {}'.format(len(chart_records)))

        return [ self._create_update_model(**args) for args in
            map(
                lambda record: {
                    'status_id':            record.status.id,
                    'movie_first_retrieve': record.status.postdate,
                    'view':                 record.view,
                    'comment':              record.comment,
                    'mylist':               record.mylist,
                    'minutes':              record.time,
                },
                chart_records
            )
        ]

    def _create_update_model(self,
        status_id: str,
        movie_first_retrieve: datetime.datetime,
        view: int,
        comment: int,
        mylist: int,
        minutes: Union[float, None]=None,
    ):
        '''
        In:
            status_id: str: id for target status record
            movie_first_retrieve: datetime: Status.first_retrieve
            view: int: Chart.view
            comment: int: Chart.comment
            mylist: int: Chart.mylist
        Out: peewee.Model() (to update)
        '''
        self.logger.debug('Target ID: {}, score seeds: V,C,M,T: {}, {}, {}, {}.'.format(status_id, view, comment, mylist, minutes))

        def backward_predict(
            view: int,
            comment: int,
            mylist: int,
            days: float,
        ) -> Tuple[float, float, float]:
            predict_seeds = np.log10(np.array((
                view + 1,
                comment + 1,
                mylist + 1,
                days,
                10
            )))
            predict_result = 10 ** (np.dot(BACKWARD_PREDICT_MATRIX, predict_seeds))

            return tuple(predict_result)

        def forward_predict(
            view: int,
            comment: int,
            mylist: int,
            minutes: float,
        ) -> Tuple[float, float, float]:
            predict_seeds = np.log10(np.array((
                view + 1,
                comment + 1,
                mylist + 1,
                minutes + 1,
                10
            )))
            predict_result = 10 ** (np.dot(FORWARD_PREDICT_MATRIX, predict_seeds))

            return tuple(predict_result)

        def calculate_score(view: float, comment: float, mylist: float) -> float:
            return np.sqrt(view) * (1 - 0.5 * 10**(-20 * comment / view)) * (1 - 0.5 * 10**(-20 * mylist / view))

        target_status = Status.get(Status.id == status_id)

        if minutes is None:
            _minutes = (datetime.datetime.now() - movie_first_retrieve).total_seconds() / 60
        else:
            _minutes = minutes

        _days = _minutes / 60 / 24

        if _days > 7:
            score_seed = backward_predict(view, comment, mylist, _days)
            score_status = -1
        elif _days < 7:
            score_seed = forward_predict(view, comment, mylist, _minutes)
            score_status = 1
        else:
            score_seed = (view, comment, mylist)
            score_status = 0

        score = calculate_score(*score_seed)

        target_status.score = score
        target_status.score_status = score_status

        return target_status
