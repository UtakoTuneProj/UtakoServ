#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from utako.exception.restricted_movie_exception import RestrictedMovieException
import subprocess as sbproc
import youtube_dl

class NicoDownloader:
    def __call__(self, mvid, retries = 5, force = False): #ランキング取得・キュー生成部
        try:
            youtube_dl.YoutubeDL({
                'outtmpl': 'tmp/mp4/%(id)s.mp4',
                'retries': retries,
            }).download([
                'http://www.nicovideo.jp/watch/{}'.format(mvid)
            ])
        except youtube_dl.utils.DownloadError as e:
            if re.compile(
                "niconico reports error: (invalid_v[123]|domestic_video)"
            ).search(e.args[0]):
                raise RestrictedMovieException(mvid)
            elif retries < 1:
                raise
            else:
                time.sleep(10)
                self(mvid, retries = retries - 1, force = force)
        else:
            process = sbproc.run([
                'ffmpeg',
                '-i', #infile
                'tmp/mp4/{}.mp4'.format(mvid),
                '-y' if force else '-n', #overwrite if force is True
                '-aq', #bitrate
                '128k',
                '-ac', #channels
                '1', #monoral
                '-ar', #sampling rate
                '44100',
                'tmp/wav/{}.wav'.format(mvid),#outfile name
            ])
            if process.returncode != 0: # if process does not stop accurately
                os.remove('tmp/mp4/{}.mp4'.format(mvid))
                time.sleep(10)
                self(mvid, retries = retries, force = force)
