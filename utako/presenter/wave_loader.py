#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from pathlib import Path
import librosa
import multiprocessing as mp

class WaveLoader:
    def __call__(self, dirpath):
        if type(dirpath) == str:
            p = Path(dirpath)
        elif issubclass(type(dirpath), Path):
            p = dirpath
        else:
            raise TypeError(
                'dirpath must be str or pathlib.Path, not {}'
                .format(type(dirpath))
            )

        proc = mp.Pool()
        train = np.array(proc.map(self.fetchone, p.glob('train/*.wav')))
        proc.close()

        proc = mp.Pool()
        test = np.array(proc.map(self.fetchone, p.glob('test/*.wav')))
        proc.close()

        return train, test

    def fetchone(self, f):
        s, _ = librosa.load(str(f))
        l = len(s)
        res = s[l//2-110250:l//2+110250]
        del s, _
        return res

    def fetch(self, isTrain = True, mvid = None):
        return self(Path('songset/'))
