#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
import subprocess as sbproc
import youtube_dl

class NicoDownloader:
    def __call__(self, mvid, max_trial = 5, force = False): #ランキング取得・キュー生成部
        youtube_dl.YoutubeDL({
            'outtmpl': 'songset/mp4/%(id)s.mp4',
            'retries': max_trial,
        }).download([
            'http://www.nicovideo.jp/watch/{}'.format(mvid)
        ])

        sbproc.run([
            'ffmpeg',
            '-i', #infile
            'songset/mp4/{}.mp4'.format(mvid),
            '-y' if force else '-n', #overwrite if force is True
            '-aq', #bitrate
            '128k',
            '-ac', #channels
            '1', #monoral
            '-ar', #sampling rate
            '44100',
            'songset/wav/{}.wav'.format(mvid),#outfile name
        ])
