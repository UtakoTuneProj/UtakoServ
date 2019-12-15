#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from peewee import fn
import youtube_dl

from utako.model.abstract_model import database
from utako.model.song_index import SongIndex
from utako.model.analyze_queue import AnalyzeQueue
from utako.presenter.song_indexer import SongIndexer

class SongIndexUpdater:
    def __call__(self, limit = 10, retries = 5, force = False): #ランキング取得・キュー生成部
        movies = AnalyzeQueue.select(
            AnalyzeQueue.movie_id,
        ).where(
            AnalyzeQueue.version == settings['model_version'],
            AnalyzeQueue.status == 0,
        ).group_by(
            AnalyzeQueue.movie_id
        ).order_by(
            -fn.Count(AnalyzeQueue.movie_id)
        ).limit(limit)
        if not force:
            subquery = SongIndex.select(SongIndex.status_id).where(SongIndex.version == settings['model_version'])
            movies = movies.where(AnalyzeQueue.movie_id.not_in(subquery))

        movie_list = [movie.movie_id for movie in movies]
        AnalyzeQueue.update(status=1).where(
            AnalyzeQueue.movie_id << movie_list
        ).execute()

        with open(settings[ 'model_structure' ]) as f:
            structure = yaml.load(f)
        si = SongIndexer(structure)

        success = []
        deleted = []
        failed = movie_list[:]
        si_update = []
        try:
            for movie in movie_list:
                try:
                    song_index = si(movie, retries = retries)
                except youtube_dl.utils.YoutubeDLError as e:
                    if e.exc_info[0] == urllib.error.HTTPError:
                        http_err = e.exc_info[1]
                        if http_err.code == 404:
                            deleted.append(movie)
                            failed.remove(movie)
                            continue
                        elif http_err.code == 403:
                            continue
                        else:
                            raise
                    else:
                        raise
                except youtube_dl.utils.DownloadError as e:
                    e.exc_info[2].tb_next
                    if re.compile("niconico reports error: invalid_v[123]$").search(e.args[0]):
                        deleted.append(movie)
                        failed.remove(movie)
                        continue
                    else:
                        raise
                else:
                    success.append(movie)
                    failed.remove(movie)
                    si_update.append(
                        [ movie ] + song_index.tolist() + [ settings['model_version'] ],
                    )
        finally:
            with database.atomic():
                if len(success + deleted) > 0:
                    AnalyzeQueue.delete().where(AnalyzeQueue.movie_id << success + deleted).execute()
                if len(failed) > 0:
                    AnalyzeQueue.update(status=0).where(AnalyzeQueue.movie_id << failed).execute()
                if len(si_update) > 0:
                    SongIndex.insert_many(si_update,fields=[
                        SongIndex.status_id,
                        SongIndex.value0,
                        SongIndex.value1,
                        SongIndex.value2,
                        SongIndex.value3,
                        SongIndex.value4,
                        SongIndex.value5,
                        SongIndex.value6,
                        SongIndex.value7,
                        SongIndex.version,
                    ]).on_conflict_replace().execute()
