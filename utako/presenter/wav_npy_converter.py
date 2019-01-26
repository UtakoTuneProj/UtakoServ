#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

import librosa
import multiprocessing as mp
from pathlib import Path

class WavNpyConverter:
    def __init__(self):
        pass

    def __call__(self, readpath = 'songset/wav', writepath = 'wav.npy', sr=5513, length=8192, duplication=8):
        wavs = list(Path(readpath).glob('**/*.wav'))

        pool_args = [{
            'path': str(w),
            'sr': sr,
            'dtype': np.float32,
        } for w in wavs]
        with mp.Pool() as pool:
            arrays = pool.map(
                self._wrap,
                pool_args,
            )

        pos = 0
        jslist = []
        npyarray = np.zeros([0,length], dtype = np.float32)
        for array, f in zip(arrays, wavs):
            i = ( array[0].shape[-1] // length ) - 1

            offset = length // duplication
            for j in range(duplication):
                npyarray = np.append(npyarray, array[0][offset*j:offset*j+length*i].reshape([i, length]), axis = 0)

            jslist.append([
                f.name,
                pos,
                pos + i * duplication
            ])
            pos += i * duplication
        
        with open(writepath+'.json', 'w') as f:
            json.dump(jslist, f, indent = 2)

        np.save(writepath, npyarray)
        
        identity = np.identity(len(jslist)).astype(np.int8)
        index = []
        for i, song in enumerate(jslist):
            index += [i for j in range(song[2] - song[1])]
        np.save(writepath + '.label.npy', identity[index, :])

    def _wrap(self, kwargs):
        return librosa.core.load(**kwargs)
