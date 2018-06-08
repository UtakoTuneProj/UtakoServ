#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.presenter.chart_updater import ChartUpdater
from utako.presenter.status_updater import StatusUpdater
from utako.presenter.song_index_updater import SongIndexUpdater

def hourly():
    StatusUpdater()()
    ChartUpdater()()

    return None
