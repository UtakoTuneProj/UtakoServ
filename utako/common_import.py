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
import MySQLdb
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
    raise KeyError('You have to specify PYTHON_ENV.')

if py_env in 'development':
    config.read('conf/auth.devel.conf')
elif py_env == 'test':
    config.read('conf/auth.test.conf')
elif py_env == 'production':
    config.read('conf/auth.conf')
else:
    raise ValueError("env variable PYTHON_ENV must be 'development', 'test' or 'prodcution', not {}".format(py_env))

with open('conf/settings.yaml') as f:
    settings = yaml.load(f)
