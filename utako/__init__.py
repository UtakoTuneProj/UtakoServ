#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging

class UtakoLogFormatter(logging.Formatter):
    def __init__(self,
        fmt='[UTAKO | %(levelname)s | %(module)s.%(funcName)s | %(asctime)-15s] %(message)s',
        datefmt=None,
        style='%'
    ):
        super().__init__(fmt, datefmt, style)

def get_root_logger():
    logger = logging.getLogger('utako')

    logger.propagate = True
    logger.setLevel('DEBUG')
    logger.addHandler(logging.StreamHandler())
    logger.handlers[-1].setFormatter(UtakoLogFormatter())
    logger.debug('New Logger has been set')

    return logger

root_logger = get_root_logger()

import utako.common_import
import utako.model
import utako.presenter
import utako.task
import utako.analyzer