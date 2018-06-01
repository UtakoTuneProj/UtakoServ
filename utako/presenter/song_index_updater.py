#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from peewee import fn

from utako.model.abstract_model import database
from utako.model.song_index import SongIndex
from utako.model.analyze_queue import AnalyzeQueue
from utako.presenter.song_indexer import SongIndexer

class SongIndexUpdater:
    def __call__(self, limit = 10): #ランキング取得・キュー生成部
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
        movie_list = [movie.movie_id for movie in movies]
        AnalyzeQueue.update(status=1).where(
            AnalyzeQueue.movie_id << movie_list
        ).execute()

        with open(settings[ 'model_structure' ]) as f:
            structure = yaml.load(f)
        si = SongIndexer(structure)

        success = []
        failed = []
        si_update = []
        for movie in movie_list:
            try:
                song_index = si(movie)
            except Exception as e:
                failed.append(movie)
            else:
                success.append(movie)
                si_update.append(
                    [ movie ] + song_index.tolist() + [ settings['model_version'] ],
                )

        with database.atomic():
            AnalyzeQueue.delete().where(AnalyzeQueue.movie_id << success).execute()
            AnalyzeQueue.update(status=0).where(AnalyzeQueue.movie_id << failed).execute()
            SongIndex.insert_many(si_update,fields=[
                SongIndex.id,
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
