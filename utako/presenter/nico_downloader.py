#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
import subprocess as sbproc

class NicoDownloader:
    def __call__(self, mvid): #ランキング取得・キュー生成部
        sbproc.run([
            'youtube-dl',
            'http://www.nicovideo.jp/watch/{}'.format(mvid),
            '-o',
            'songset/mp4/{}.mp4'.format(mvid),
        ])
        sbproc.run([
            'ffmpeg',
            '-i',
            'songset/mp4/{}.mp4'.format(mvid),
            '-aq',
            '128k',
            '-ac',
            '1',
            '-ar',
            '44100',
            'songset/wav/{}.wav'.format(mvid),
        ])
