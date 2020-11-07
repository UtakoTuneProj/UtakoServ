#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from utako import root_logger as logger

from utako.presenter.score_updater import ScoreUpdater
from utako.model.abstract_model import database

def update_song_score():
    sent_movies = ScoreUpdater()()
    logger.info(
        'ScoreUpdater triggered. Queued Movie: %i',
        sent_movies
    )

    return sent_movies
