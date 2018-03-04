#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import utako
import yaml
import gc

def sae_test(fname = 'conf/sae.yaml', **kwargs):
    with open(fname) as f:
        structure = yaml.load(f)
    SAE = \
        utako.analyzer.song_auto_encoder.SongAutoEncoder(
            structure = structure,
            **kwargs
        )
    SAE.learn()
    gc.collect()

if __name__ == '__main__':
    sae_test()
