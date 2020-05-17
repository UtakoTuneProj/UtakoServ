#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from utako import root_logger as logger

from utako.presenter.status_updater import StatusUpdater
from utako.presenter.chart_updater import ChartUpdater
from utako.presenter.score_updater import ScoreUpdater
from utako.model.abstract_model import database

def hourly():
    try:
        status_results = StatusUpdater()()
        logger.info(
            'StatusUpdater finished. Inserted Rows: %i',
            status_results['inserted_row_counts']
        )

        chart_results = ChartUpdater()()
        logger.info(
            'ChartUpdater finished. Today: %i, LastWeek: %i',
            len(chart_results['today']),
            len(chart_results['lastweek'])
        )

        score_results = ScoreUpdater()()
        logger.info(
            'ScoreUpdater finished. Updated Score: %i',
            len(score_results)
        )
    finally:
        database.close()

    return {
        'status_results': status_results,
        'chart_results': chart_results,
        'score_results': score_results,
    }
