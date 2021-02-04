#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from utako import root_logger
from peewee import fn
import youtube_dl

from utako.model.abstract_model import database
from utako.model.song_index import SongIndex
from utako.model.analyze_queue import AnalyzeQueue
from utako.model.status import Status
from utako.presenter.song_indexer import SongIndexer
from utako.exception.restricted_movie_exception import RestrictedMovieException
from utako.exception.index_core_not_found_exception import IndexCoreNotFoundException

class SongIndexUpdater:
    def __call__(self, limit = 10, retries = 5, force = False): #ランキング取得・キュー生成部
        movie_ids = self._fetch_analyze_queue(limit)
        return self.index_by_movie_ids(movie_ids, retries=retries, is_forced=force)

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

    def _fetch_already_analyzed_movies(self, movie_ids, version):
        index_records = SongIndex.select(
            SongIndex.status_id
        ).where(
            SongIndex.version == version,
            SongIndex.status_id << movie_ids
        ).execute()
        return [song_index.status_id.id for song_index in index_records]

    def _fetch_queue_ongoing_movies(self, movie_ids):
        queue_records = AnalyzeQueue.select(
            AnalyzeQueue.movie_id
        ).where(
            AnalyzeQueue.movie_id << movie_ids,
            AnalyzeQueue.status == 1,
        ).group_by(
            AnalyzeQueue.movie_id
        ).execute()
        return [queue.movie_id.id for queue in queue_records]

    def index_by_movie_ids(
        self,
        movie_ids,
        retries=0,
        is_forced=False
    ):

        version = settings['model_version']
        skipped = self._fetch_queue_ongoing_movies(movie_ids)
        if not is_forced:
            skipped += self._fetch_already_analyzed_movies(movie_ids, version)

        filtered_movie_ids = list(set(movie_ids) - set(skipped))
        AnalyzeQueue.update(
            status=1
        ).where(
            AnalyzeQueue.movie_id << filtered_movie_ids
        ).execute()

        with open(settings[ 'model_structure' ]) as f:
            structure = yaml.safe_load(f)
        si = SongIndexer(structure)

        failed = filtered_movie_ids[:]
        success = []
        deleted = []
        timeout = []
        si_update = []

        try:
            for movie_id in filtered_movie_ids:
                root_logger.debug('Analyzing for {}'.format(movie_id))
                try:
                    song_index = si(movie_id, retries = retries)
                except youtube_dl.utils.YoutubeDLError as e:
                    root_logger.warning(e)
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
                except IndexCoreNotFoundException as e:
                    root_logger.warning(e.message)
                    deleted.append(movie_id)
                    failed.remove(movie_id)
                    continue
                except TimeoutError as e:
                    timeout.append(movie_id)
                    failed.remove(movie_id)
                    continue
                else:
                    root_logger.debug('Analyze complete for {}'.format(movie_id))
                    success.append(movie_id)
                    failed.remove(movie_id)
                    si_update.append(
                        [ movie_id ] + song_index.tolist() + [ version ],
                    )
        finally:
            with database.atomic():
                if len(success + deleted) > 0:
                    AnalyzeQueue.delete().where(AnalyzeQueue.movie_id << success + deleted).execute()
                if len(failed + timeout) > 0:
                    AnalyzeQueue.update(status=0).where(AnalyzeQueue.movie_id << failed + timeout).execute()
                if len(deleted) > 0:
                    Status.update(validity=0).where(Status.id << deleted).execute()
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
            'timeout': timeout,
            'deleted': deleted,
            'skipped': skipped
        }
