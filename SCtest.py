#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __init__ import utako, yaml, np, gc, wav, songs_label

def sc_test(
    fname = 'conf/sc.yaml',
    wav = wav,
    label = songs_label,
    n_train = 100000,
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
    SC = \
        utako.analyzer.song_classifier.SongClassifier(
            structure = structure,
            x_train = wav[train_index, :],
            y_train = label[train_index],
            x_test  = wav[test_index, :],
            y_test  = label[test_index],
            **kwargs
        )
    SC.learn()
    gc.collect()

    return SC, train_index, test_index

if __name__ == '__main__':
    sc_test(
        isgui = True,
#       isgpu = False,
        n_epoch = 100,
        batchsize = 100 
    )

