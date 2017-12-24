#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.presenter.chart_updater import ChartUpdater
from utako.presenter.status_updater import StatusUpdater

def hourly():
    StatusUpdater()()
    ChartUpdater()()

    return None
