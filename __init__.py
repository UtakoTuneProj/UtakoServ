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

def load_datasets():
    wav = np.load('wav.major.npy')
    tags_label = np.load('wav.tags.npy')
    songs_label = np.load('wav.major.npy.label.npy')
    with open('wav.tags.npy.order.super.json') as f:
        sp_tags = json.load(f)

    return {
        "wav": wav,
        "tags_label": tags_label,
        "songs_label": songs_label,
        "sp_tags": sp_tags
    }
