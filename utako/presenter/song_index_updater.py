#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from utako import root_logger
from peewee import fn
import youtube_dl

from utako.model.abstract_model import database
from utako.model.song_index import SongIndex
from utako.model.analyze_queue import AnalyzeQueue
from utako.presenter.song_indexer import SongIndexer
from utako.exception.restricted_movie_exception import RestrictedMovieException

class SongIndexUpdater:
    def __call__(self, limit = 10, retries = 5, force = False): #ランキング取得・キュー生成部
        movie_ids = self._fetch_analyze_queue(limit)
        version = settings['model_version']
        return self.index_by_movie_ids(movie_ids, version=version, retries=retries, is_forced=force)

    def _fetch_analyze_queue(self, limit):
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

        return [movie.movie_id.id for movie in movies]

    def index_by_movie_ids(
        self,
        movie_ids,
        version=settings['model_version'],
        retries=5,
        is_forced=False
    ):

        queue_records = AnalyzeQueue.select(
            AnalyzeQueue.movie_id
        ).where(
            AnalyzeQueue.movie_id << movie_ids,
            AnalyzeQueue.status == 1,
        ).execute()

        skipped = [queue.movie_id.id for queue in queue_records]

        if not is_forced:
            index_records = SongIndex.select(
                SongIndex.status_id
            ).where(
                SongIndex.version == version,
                SongIndex.status_id << movie_ids
            ).execute()

            skipped += [song_index.status_id.id for song_index in index_records]

        filtered_movie_ids = list(set(movie_ids) - set(skipped))

        with open(settings[ 'model_structure' ]) as f:
            structure = yaml.load(f)
        si = SongIndexer(structure)

        success = []
        deleted = []
        failed = filtered_movie_ids[:]
        si_update = []

        try:
            for movie_id in filtered_movie_ids:
                root_logger.debug('Analyzing for {}'.format(movie_id))
                try:
                    song_index = si(movie_id, retries = retries)
                except youtube_dl.utils.YoutubeDLError as e:
                    root_logger.warning(e.message)
                    if e.exc_info[0] == urllib.error.HTTPError:
                        http_err = e.exc_info[1]
                        if http_err.code == 404:
                            deleted.append(movie_id)
                            failed.remove(movie_id)
                            continue
                        elif http_err.code == 403:
                            continue
                        else:
                            raise
                    else:
                        raise
                except RestrictedMovieException as e:
                    root_logger.warning(e.message)
                    deleted.append(movie_id)
                    failed.remove(movie_id)
                    continue
                else:
                    root_logger.debug('Analyze complete for {}'.format(movie_id))
                    success.append(movie_id)
                    failed.remove(movie_id)
                    si_update.append(
                        [ movie_id ] + song_index.tolist() + [ settings['model_version'] ],
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

        return {
            'succeeded': success,
            'failed': failed,
            'deleted': deleted,
            'skipped': skipped
        }
