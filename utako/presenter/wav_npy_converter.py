#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.model.status import Status

from scipy.signal import spectrogram
import librosa
import multiprocessing as mp
from pathlib import Path

class WavNpyConverter:
    def __init__(self):
        pass

    def __call__(
        self,
        movies_use,
        readpath = 'songset/wav',
        writepath = 'wav.npy',
        sr=4096,
        length=8192,
        duplication=4,
        songs_limit=10,
        length_limit=100,
    ):
        wavs = list(map(lambda mvid: Path(readpath) / '{}.wav'.format(mvid), movies_use))
        if len(wavs) > songs_limit:
            wavs = wavs[:songs_limit]

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
        widths = tuple( map(lambda x: min( ( x[0].shape[-1] // length - 1 ) * duplication, length_limit ), arrays) )
        npyarray = np.memmap(writepath, mode='w+', dtype=np.float32, shape=(sum(widths),1,length))
        for array, mvid, w in zip(arrays, movies_use, widths):
            for j in range(duplication):
                start_pos = length // duplication * j
                partial_count = (w-j-1) // duplication + 1
                end_pos = start_pos + length *partial_count 
                npyarray[j:w:duplication, :] = \
                    array[0][start_pos:end_pos].reshape([partial_count, 1, length])

            jslist.append([
                mvid,
                pos,
                pos + w
            ])
            pos += w
        
        with open(writepath+'.json', 'w') as f:
            json.dump(jslist, f, indent = 2)
        
        index = np.zeros([sum(widths)], dtype = np.int32)
        score = np.zeros([sum(widths)], dtype = np.float32)
        for i, song in enumerate(jslist):
            index[song[1]:song[2]] = i
            score[song[1]:song[2]] = Status.get_by_id(song[0]).score
        np.save(writepath + '.label.npy', index)
        np.save(writepath + '.score.npy', score)
        del index
        del score

        spectro_shape = spectrogram(npyarray[0, :], window='hamming', mode='magnitude')[2].shape
        spectro = np.zeros([ npyarray.shape[0] ] + list(spectro_shape), dtype = np.float32)
        for i in range(npyarray.shape[0]):
            spectro[i, :] = np.log10( spectrogram(npyarray[i, :], window='hamming', mode='magnitude')[2] )
        np.save(writepath + '.spectro.npy', spectro)
        del spectro

    def _wrap(self, kwargs):
        return librosa.core.load(**kwargs)
