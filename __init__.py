#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import utako
import yaml
import json
import numpy as np
import gc
import chainer
import importlib as imp
from pathlib import Path

DATASET_DIR="datasets"
DATASET_NAME="chronicle.2019.03"

basedir=Path(DATASET_DIR) / DATASET_NAME
dataset_info = json.load((basedir/'info.json').open())

wav = np.memmap(
    str( basedir/'wav.memmap' ),
    mode='r',
    dtype=np.float32
).reshape((-1,1,dataset_info['length_per_sample']))
songs_label = np.load(
    str(basedir/'label.npy'),
    mmap_mode='r'
)

tags_label = np.load('datasets/wav.tags.npy', mmap_mode='r')
with open('datasets/wav.tags.npy.order.super.json') as f:
    sp_tags = json.load(f)

import PUTC
import SAEtest
import SCtest
