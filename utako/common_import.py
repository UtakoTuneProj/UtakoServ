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

from chainer import cuda, Variable, optimizers, Chain, ChainList
import chainer.functions  as F
import chainer.links as L
import MySQLdb
import numpy as np
import scipy.cluster
import tweepy
import yaml

config = configparser.ConfigParser()
config.read('conf/auth.conf')
