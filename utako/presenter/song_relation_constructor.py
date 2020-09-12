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
    def __call__(self, max_relations = 13):
        self.construct_kdtree()
        relations = self.get_all_relations(max_relations)
        return self.store_relations(relations)

    def recalculate_for(self, movie_id, max_relations=13):
        self.construct_kdtree()
        relations = self.get_relations_from_movie_id(movie_id, max_relations)
        return self.store_relations(relations)

    def construct_kdtree(self):
        query = SongIndex.select().where(
            SongIndex.version == settings['model_version']
        ).tuples()

        self.movies = np.array([q[1] for q in query], dtype=str)
        self.positions = np.array([q[2:10] for q in query], dtype=np.float64)
        self.kd_tree = KDTree(self.positions)

    def get_all_relations(self, k):
        origins = np.array([[i for j in range(k)] for i in range(self.positions.shape[0])])
        distances, destinations = self.kd_tree.query(self.positions, k = k)
        relations = np.array((origins, destinations, distances*1000), dtype=np.int32).reshape((3,-1)).T
        mask = [ False
                if (k[1::-1] == relations[...,0:2]).all(axis=-1).any()
                and k[0] >= k[1]
                else True
                for k in relations]
        return relations[mask]

    def get_relations_from_movie_id(self, movie_id, k):
        origin_index = self.get_index_from_movie_id(movie_id)
        distances, destinations = self.kd_tree.query(self.positions[origin_index].reshape(1,-1), k = k)

        origin_index_map = np.array([ origin_index for _ in range(k) ]).reshape(1,-1)

        relations = np.array((
            origin_index_map,
            destinations,
            distances*1000
        ), dtype=np.int32).reshape((3,-1)).T

        mask = ( destinations != origin_index ).reshape(-1)

        return relations[mask]

    def get_index_from_movie_id(self, movie_id):
        movie_index = np.argwhere(self.movies == movie_id).reshape(-1)

        if movie_index.shape[0] != 1:
            raise ValueError
        else:
            return movie_index[0]

    def store_relations(self, relations):
        '''
        In:
            relations: np.array(dtype=np.int32, shape=(3, -1))
                nparray contains origin, destinations, distance
                each origin/destinations value are indices of movie
        Out: inserted_count: int
            number of newly created song_relation record
        '''
        ssr_target = []
        def create(rel):
            record = SongRelation.create(
                distance = rel[2],
                version = settings['model_version']
            )
            return [{
                'status': self.movies[rel[0]],
                'song_relation': record.id
            },{
                'status': self.movies[rel[1]],
                'song_relation': record.id
            }]

        Origin = StatusSongRelation.alias()
        Destination = StatusSongRelation.alias()
        pb = ProgressBar()

        with database.atomic():
            for origin_index in pb(np.unique(relations[...,0])):
                origin_id = self.movies[origin_index]
                related_relations = relations[relations[...,0] == origin_index]

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
                existing_movie_id_indices = np.argwhere(np.isin(self.movies, tuple(existing_relations)))

                new_relation = related_relations[
                    np.logical_not(np.isin(related_relations[...,1], existing_movie_id_indices))
                ]

                flatten = lambda l: sum(l, [])
                ssr_target += flatten([ create(rel) for rel in new_relation ])

            if len(ssr_target) != 0:
                StatusSongRelation.insert_many(ssr_target).execute()

        return len(ssr_target) // 2
