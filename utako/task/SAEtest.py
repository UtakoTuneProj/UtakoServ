#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.presenter.chart_updater import ChartUpdater
from utako.presenter.status_updater import StatusUpdater

def sae_test():
    SAEs = {}
    
    for keym in abstmodel:
        for keyp in processing:
            for keys in structure:
                SAEs[(keym, keyp, keys)] = \
                    utako.analyzer.song_auto_encoder.SongAutoEncoder(
                        structure[keys],
                        n_epoch = 1000,
                        isgui = False,
                        preprocess = processing[keyp][0],
                        postprocess = processing[keyp][1],
                        modelclass = abstmodel[keym],
                        name = '{}_{}_{}'.format(keym, keyp, keys)
                    )
                    SAEs[(keym, keyp, keys)].learn()
                gc.collect()
