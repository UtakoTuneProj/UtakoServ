# -*- coding: utf-8 -*-
from logging import getLogger, Formatter
from logging.handlers import RotatingFileHandler
from logging.config import fileConfig
from logging import DEBUG, INFO, WARNING, ERROR, CRITICAL
import os
import sys
import configparser

_op = os.path

class UtakoFormatter(Formatter):
    def format(self, record):
        s = super().format(record)
        s = s.replace('\n', '\n' + ' '*8 + '| ')
        return s

rootlogger = getLogger()
fileConfig('conf/logger.conf')

if __name__ == '__main__':
    rootlogger.warning('WARNING TEST\nWARNING TEST')
    rootlogger.error('ERROR TEST\nERROR TEST')
    rootlogger.critical('CRITICAL TEST\nCRITICAL TEST')
