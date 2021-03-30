#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from utako import root_logger as logger

from utako.presenter.chart_updater import ChartUpdater
from utako.model.abstract_model import database

def check_chart():
    try:
        chart_results = ChartUpdater()()
        logger.info(
            'ChartUpdater finished. Today: %i, LastWeek: %i',
            len(chart_results['today']),
            len(chart_results['lastweek'])
        )
    finally:
        database.close()

    return {
        'chart_results': chart_results,
    }
