#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
from pythonjsonlogger import jsonlogger

class UtakoLogStringFormatter(logging.Formatter):
    def __init__(self,
        fmt='[UTAKO | %(levelname)s | %(module)s.%(funcName)s | %(asctime)-15s] %(message)s',
        datefmt=None,
        style='%'
    ):
        super().__init__(fmt, datefmt, style)

class UtakoLogJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        log_record['severity'] = record.levelname
        log_record['logging.googleapis.com/sourceLocation'] = {
            'file': record.pathname,
            'line': str(record.lineno),
            'function': record.funcName,
        }

def get_root_logger():
    logger = logging.getLogger('utako')

    logger.propagate = True
    logger.setLevel('DEBUG')
    logger.addHandler(logging.StreamHandler())
    logger.handlers[-1].setFormatter(UtakoLogJsonFormatter())
    logger.debug('New Logger has been set')

    return logger

root_logger = get_root_logger()

import utako.common_import
import utako.model
import utako.presenter
import utako.task
import utako.analyzer
import utako.api
import utako.delegator