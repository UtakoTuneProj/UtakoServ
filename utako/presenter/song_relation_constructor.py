#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako import root_logger
from utako.common_import import *
from utako.model.abstract_model import database
from utako.model.song_index import SongIndex
from utako.model.song_relation import SongRelation
from utako.model.status_song_relation import StatusSongRelation
from sklearn.neighbors import KDTree

class SongRelationConstructor:
    def __call__(self, max_relations = 11):
        movies, positions = self.fetch_indexes()
        relations = self.get_relations(positions, max_relations)
        self.store_all_relations(movies, relations)

    def recalculate_for(self, movie_id, max_relations=11):
        movies, positions = self.fetch_indexes()
        relations = self.get_relations(positions, max_relations)
        return self.store_relations_for([ movie_id ], movies, relations)

    def fetch_indexes(self):
        query = SongIndex.select().where(
            SongIndex.version == settings['model_version']
        ).tuples()
        movies = np.array([q[1] for q in query], dtype=str)
        positions = np.array([q[2:10] for q in query], dtype=np.float64)
        return movies, positions

    def get_relations(self, positions, k):
        kdt = KDTree(positions)
        origins = np.array([[i for j in range(k)] for i in range(positions.shape[0])])
        distances, destinations = kdt.query(positions, k = k)
        relations = np.array((origins, destinations, distances*1000), dtype=np.int32).reshape((3,-1)).T
        mask = [ False
                if (k[1::-1] == relations[...,0:2]).all(axis=-1).any()
                and k[0] >= k[1]
                else True
                for k in relations]
        return relations[mask]

    def store_all_relations(self, movies, relations):
        return self.store_relation(movies, movies, relations)

    def store_relations_for(self, target_movie_ids, movies, relations):
        '''
        In:
            target_movie_ids: iterable(dtype=str)
                iterable object contains movie_ids to store relations
            movies: np.array(dtype=str)
                nparray for movie_ids included in relations
            relations: np.array(dtype=np.int32, shape=(3, -1))
                nparray contains origin, destinations, distance
                each origin/destinations value are indices of movie
        Out: (None)
        '''
        ssr_target = []
        def create(movies, rel):
            record = SongRelation.create(
                distance = rel[2],
                version = settings['model_version']
            )
            return [{
                'status': movies[rel[0]],
                'song_relation': record.id
            },{
                'status': movies[rel[1]],
                'song_relation': record.id
            }]

        Origin = StatusSongRelation.alias()
        Destination = StatusSongRelation.alias()
        pb = ProgressBar()

        with database.atomic():
            for origin_id in pb(target_movie_ids):
                origin_id_index = np.argwhere(movies == origin_id).reshape(-1)
                if origin_id_index.shape[0] == 0:
                    root_logger.warn('Skipped for not found movie {}. Maybe not analyzed?'.format(origin_id))
                    continue

                related_relations = relations[relations[...,0] == origin_id_index[0]]
                if related_relations.shape[0] == 0:
                    continue

                existing_relations = Origin.select(
                    Destination.status
                ).join(
                    SongRelation
                ).join(
                    Destination, on=(
                        Origin.song_relation == Destination.song_relation
                    )
                ).where(
                    Origin.status == origin_id,
                    SongRelation.version == settings['model_version'],
                ).tuples()
                existing_movie_id_indices = np.argwhere(np.isin(movies, tuple(existing_relations)))

                new_relation = related_relations[
                    np.logical_not(np.isin(related_relations[...,1], existing_movie_id_indices))
                ]

                flatten = lambda l: sum(l, [])
                ssr_target += flatten([ create(movies, rel) for rel in new_relation ])

            if len(ssr_target) != 0:
                StatusSongRelation.insert_many(ssr_target).execute()

        return len(ssr_target) // 2
