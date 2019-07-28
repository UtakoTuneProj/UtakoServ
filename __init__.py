#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import utako
import yaml
import json
import numpy as np
import gc
import chainer
import importlib as imp

wav = np.load('datasets/wav.major.npy', mmap_mode='r')
tags_label = np.load('datasets/wav.tags.npy', mmap_mode='r')
songs_label = np.load('datasets/wav.major.npy.label.npy', mmap_mode='r')
with open('datasets/wav.tags.npy.order.super.json') as f:
    sp_tags = json.load(f)

import PUTC
import SAEtest
import SCtest
