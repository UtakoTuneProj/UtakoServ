#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.presenter.status_updater import StatusUpdater
from utako.presenter.chart_updater import ChartUpdater
from utako.presenter.score_updater import ScoreUpdater

def hourly():
    StatusUpdater()()
    ChartUpdater()()
    ScoreUpdater()()

    return None
