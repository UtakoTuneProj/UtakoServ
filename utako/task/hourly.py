#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.presenter.status_updater import StatusUpdater
from utako.presenter.chart_updater import ChartUpdater
from utako.presenter.score_updater import ScoreUpdater
from utako.model.abstract_model import database

def hourly():
    try:
        status_results = StatusUpdater()()
        chart_results = ChartUpdater()()
        score_results = ScoreUpdater()()
    finally:
        database.close()

    return {
        'status_results': status_results,
        'chart_results': chart_results,
        'score_results': score_results,
    }
