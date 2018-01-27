#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from pathlib import Path
import librosa
import multiprocessing as mp

class WaveLoader:
    def __call__(self, dirpath, length = 262144):
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
        fs = tuple(p.glob('train/*.wav'))
        length_wrap = [length for i in range(len(fs))]
        train = np.array(proc.map(self.fetch_wrap, zip(fs, length_wrap)), dtype = np.float32)
        proc.close()

        proc = mp.Pool()
        fs = tuple(p.glob('test/*.wav'))
        length_wrap = [length for i in range(len(fs))]
        test = np.array(proc.map(self.fetch_wrap, zip(fs, length_wrap)), dtype = np.float32)
        proc.close()

        return train, test

    def fetchone(self, f, length):
        half = length // 2
        s, _ = librosa.load(str(f))
        l = len(s)
        res = s[
            l//2 - half
            : l//2 + half + length%2]
        del s, _
        return res

    def fetch_wrap(self, arg):
        return self.fetchone(*arg)

    def fetch(self, isTrain = True, mvid = None):
        return self(Path('songset/'))
