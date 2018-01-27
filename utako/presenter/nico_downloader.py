#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
import subprocess as sbproc

class NicoDownloader:
    def __call__(self, mvid): #ランキング取得・キュー生成部
        sbproc.run([
            'youtube-dl',
            'https://www.nicovideo.jp/watch/{}'.format(mvid),
            '-u',
            config['niconico']['user'],
            '-p',
            config['niconico']['password'],
            '-x',
            '-ar',  #sampling rate
            '44100',
            '-ac',  #channels
            '1',    #monoral
            '-ab',  #bitrate
            '128k'
            '--audio-format',
            'wav',
            '-o',
            '%(id)s.mp4',
        ])
