#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime

class TimedateConverter:
    def __call__(self, nicodate): #ニコ動形式の時刻をPython内部時刻形式に変換
        return datetime.datetime.strptime(nicodate,"%Y-%m-%dT%H:%M:%S+09:00")

    def __repr__(self):
        return('<Utako TimedateConverter>')

