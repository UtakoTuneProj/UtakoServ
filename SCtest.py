#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import utako
import yaml
import numpy as np
import gc

def sc_test(fname = 'conf/sc.yaml', **kwargs):
    with open(fname) as f:
        structure = yaml.load(f)
    wav = np.load('wav.npy')
    label = np.load('wav.label.npy')
    index = np.random.permutation(wav.shape[0])
    train_index = index[:10000]
    test_index = index[10000:12000]
    SC = \
        utako.analyzer.song_classifier.SongClassifier(
            structure = structure,
            x_train = wav[train_index, :],
            y_train = label[train_index, :],
            x_test  = wav[test_index, :],
            y_test  = label[test_index, :],
            **kwargs
        )
    SC.learn()
    gc.collect()

if __name__ == '__main__':
    sc_test(
        isgui = True,
        n_epoch = 20,
        batchsize = 100
    )

