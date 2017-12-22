#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
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
