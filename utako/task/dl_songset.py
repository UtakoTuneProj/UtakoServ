#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.model.chart import Chart
from utako.presenter.nico_downloader import NicoDownloader

def dl_songset(limit = 5000):
    movies = Chart.select().where(
        Chart.epoch == 24,
        Chart.view > limit
    ).execute()

    ndl = NicoDownloader()
    for mvid in movies:
        try_count = 0
        while try_count < 5:
            try:
                ndl(mvid.id)
            except:
                try_count += 1
                raise
            else:
                break
        else:
            print(mvid)
