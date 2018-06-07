#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
        self.store_relations(movies, relations)

    def fetch_indexes(self):
        query = SongIndex.select().where(
            SongIndex.version == settings['model_version']
        ).tuples()
        movies = []
        positions = []
        for q in query:
            movies.append(q[0])
            positions.append(q[1:9])
        movies = np.array(movies, dtype = str)
        positions = np.array(positions, dtype = np.float64)
        return movies, positions

    def get_relations(self, positions, k):
        kdt = KDTree(positions)
        origins = np.array([[i for j in range(k)] for i in range(positions.shape[0])])
        distances, destinations = kdt.query(positions, k = k)
        # distances.shape = positions.shape[:-1] + (k,)
        # destinations.shape = positions.shape[:-1] + (k,)
        relations = np.array((origins, destinations, distances*1000), dtype=np.int32).reshape((3,-1)).T
        mask = [ False
                if (k[1::-1] == relations[...,0:2]).all(axis=-1).any()
                and k[0] >= k[1]
                else True
                for k in relations]
        return relations[mask]

    def store_relations(self, movies, relations):
        Origin = StatusSongRelation.alias()
        Destination = StatusSongRelation.alias()
        with database.atomic():
            for rel in relations:
                origin_id = movies[rel[0]]
                destination_id = movies[rel[1]]
                query = Origin.select(
                    Origin.status, Destination.status, SongRelation
                ).join(
                    Destination, on=(
                        Origin.song_relation == Destination.song_relation
                    )
                ).join(
                    SongRelation
                ).where(
                    ( Origin.status != Destination.status, )
                    & ( Origin.status == origin_id )
                    & ( Destination.status == destination_id )
                )
                if not query.exists():
                    self.create(movies, rel)
                elif query.get().version < settings['model_version']:
                    self.create(movies, rel)
                elif query.get().distance != rel[2]:
                    raise

        def create(movies, rel):
            r = SongRelation.create(
                distance = rel[2],
                version = settings['model_version']
            )
            StatusSongRelation.insert_many([{
                'status': movies[rel[0]],
                'song_relation': r.id
            },{
                'status': movies[rel[1]],
                'song_relation': r.id
            }]).execute()
