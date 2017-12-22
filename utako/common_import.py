#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import codecs
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
import sqlalchemy as alch
import sqlalchemy.sql as alchsql
import sqlalchemy.exc as alchexc
from sqlalchemy.orm.session import sessionmaker
import tweepy
