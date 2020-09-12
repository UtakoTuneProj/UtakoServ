#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from utako import root_logger as logger

from utako.presenter.score_updater import ScoreUpdater
from utako.model.abstract_model import database

def update_song_score():
    try:
        score_results = ScoreUpdater()()
        logger.info(
            'ScoreUpdater finished. Updated Score: %i',
            len(score_results)
        )
    finally:
        database.close()

    return {
        'score_results': score_results,
    }
