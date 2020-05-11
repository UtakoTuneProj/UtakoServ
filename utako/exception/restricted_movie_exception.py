#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class RestrictedMovieException(Exception):
    def __init__(self, movie_id):
        self.movie_id = movie_id
        self.message = "id: {} is restricted to analyze".format(movie_id)
        Exception.__init__(self, self.message)
