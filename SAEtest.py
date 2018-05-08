#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import utako
import yaml
import numpy as np
import gc

wav = np.load('wav.npy')

def sae_test(
    fname = 'conf/sae.yaml',
    wav = wav,
    n_train = 90000,
    n_test = 10000,
    randomize = True,
    **kwargs
):
    with open(fname) as f:
        structure = yaml.load(f)
    
    if wav is None:
        print('loading wav.npy')
        wav = np.load('wav.npy')

    if randomize:
        index = np.random.permutation(wav.shape[0])
    else:
        index = np.arange(wav.shape[0])
    train_index = index[:n_train]
    test_index = index[n_train:n_train + n_test]
    SAE = \
        utako.analyzer.song_auto_encoder.SongAutoEncoder(
            structure = structure,
            x_train = wav[train_index, :],
            x_test  = wav[test_index, :],
            **kwargs
        )
    SAE.learn()
    gc.collect()

if __name__ == '__main__':
    sae_test(
        isgui = False,
#       isgpu = False,
        n_epoch = 100,
        batchsize = 20
    )

