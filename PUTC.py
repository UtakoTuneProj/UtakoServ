#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import utako
import yaml
import numpy as np
import gc

wav = np.load('wav.npy')
label = np.load('wav.tags.npy')

def putc_test(
    fname = 'conf/putc.yaml',
    wav = wav,
    label = label,
    n_train = 90000,
    n_test = 10000,
    randomize = True,
    **kwargs
):
    with open(fname) as f:
        structure = yaml.load(f)

    if randomize:
        index = np.random.permutation(wav.shape[0])
    else:
        index = np.arange(wav.shape[0])
    train_index = index[:n_train]
    test_index = index[n_train:n_train + n_test]
    PUTC = \
        utako.analyzer.pu_tag_classifier.PUTagClassifier(
            structure = structure,
            x_train = wav[train_index, :],
            y_train = label[train_index, :],
            x_test  = wav[test_index, :],
            y_test  = label[test_index, :],
            **kwargs
        )
    PUTC.learn()
    gc.collect()

    return PUTC, train_index, test_index

if __name__ == '__main__':
    putc_test(
        isgui = True,
#       isgpu = False,
        n_epoch = 100,
        batchsize = 25
    )

