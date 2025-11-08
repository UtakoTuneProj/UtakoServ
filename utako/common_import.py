#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import codecs
import configparser
import datetime
import glob
import json
import os
from progressbar import ProgressBar
import random
import re
import sys
import struct
import time
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET

from chainer import cuda, Variable, optimizers, serializers, Chain, ChainList
import chainer.functions  as F
import chainer.links as L
import numpy as np
import scipy.cluster
import tweepy
import yaml

try:
    cupy = cuda.cupy
except AttributeError:
    cupy = np

config = configparser.ConfigParser()

try:
    py_env = os.environ["PYTHON_ENV"]
except KeyError:
    py_env = "test"

conf_files = {
    'development': {
        'auth': 'conf/auth.develop.conf',
        'settings': 'conf/settings.yaml',
    },
    'production': {
        'auth': 'conf/auth.production.conf',
        'settings': 'conf/settings.yaml',
    },
    'test': {
        'auth': 'conf/auth.test.conf',
        'settings': 'conf/settings.test.yaml',
    }
}

if py_env in [ 'development', 'develop', 'devel' ]:
    conf_file = conf_files['development']
else:
    try:
        conf_file = conf_files[py_env]
    except IndexError:
        raise ValueError("env variable PYTHON_ENV must be 'development', 'test' or 'prodcution', not {}".format(py_env))

config.read(conf_file['auth'])
with open(conf_file['settings']) as f:
    settings = yaml.safe_load(f)