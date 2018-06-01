#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import utako
import yaml
import json
import numpy as np
import gc
import chainer
from progressbar import ProgressBar
import importlib as imp

wav = np.load('wav.major.npy')
tags_label = np.load('wav.tags.npy')
songs_label = np.load('wav.major.npy.label.npy')
with open('wav.tags.npy.order.super.json') as f:
    sp_tags = json.load(f)

import PUTC
import SAEtest
import SCtest
