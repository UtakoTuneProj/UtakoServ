# -*- coding: utf-8 -*-
from logging import getLogger, Formatter
from logging.handlers import RotatingFileHandler
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
import os
import sys

_op = os.path

class UtakoFormatter(Formatter):
    def format(self, record):
        s = super().format(record)
        s = s.replace('\n', '\n' + ' '*8 + '| ')
        return s

def main():
    logger = getLogger()
    formatter = UtakoFormatter(
        '{levelname:<8}| {message}', style = '{'
    )

    if not _op.isdir(_op.join(sys.path[0], 'logs/')):
        os.mkdir(_op.join(sys.path[0], 'logs/'))
    handler = RotatingFileHandler(
        _op.join(sys.path[0], 'logs/utako.log'),
        maxBytes = 65536,
        backupCount = 3
    )
    handler.setLevel(DEBUG)
    handler.setFormatter(formatter)
    logger.setLevel(WARNING)
    logger.addHandler(handler)

    return logger

logger = main()
