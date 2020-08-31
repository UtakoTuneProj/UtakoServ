#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class IndexCoreNotFoundException(Exception):
    def __init__(self, movie_id):
        Exception.__init__(self)
        self.movie_id = movie_id
        self.message = "utako can't find song core from id: {}".format(movie_id)
