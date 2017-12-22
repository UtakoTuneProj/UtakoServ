#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime

class TimedateConverter:
    def nico2datetime(self, nicodate): #ニコ動形式の時刻をPython内部時刻形式に変換
        return datetime.datetime.strptime(nicodate,"%Y-%m-%dT%H:%M:%S+09:00")

    def str2datetime(self, time12): #12桁時刻方式をPython内部時刻形式に変換
        return datetime.datetime.strptime(time12,"%Y%m%d%H%M")

    def datetime2str(self, dt): #Python内部時刻形式を12桁時刻方式に変換
        return dt.strftime("%Y%m%d%H%M")

    def datetime2nico(self, dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%S")

    def __repr__(self):
        return('<Utako TimedateConverter>')

