#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from utako import root_logger as logger

from utako.presenter.status_updater import StatusUpdater
from utako.model.abstract_model import database

def check_status():
    try:
        status_results = StatusUpdater()()
        logger.info(
            'StatusUpdater finished. Inserted Rows: %i',
            status_results['inserted_row_counts']
        )

    finally:
        database.close()

    return {
        'status_results': status_results,
    }
