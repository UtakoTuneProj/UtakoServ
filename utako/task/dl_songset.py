#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.model.chart import Chart
from utako.model.status import Status
from utako.presenter.nico_downloader import NicoDownloader

def dl_songset(limit = 5000):
    movies = Chart.select(
        Status.id
    ).join(
        Status, on = (Chart.id == Status.id)
    ).where(
        Chart.epoch == 24,
        Chart.view > limit,
        Status.validity == True,
    ).execute()

    ndl = NicoDownloader()
    for mvid in movies:
        ndl(mvid.id)
