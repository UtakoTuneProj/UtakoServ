#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.model.status import Status

from scipy.signal import spectrogram
import librosa
import multiprocessing as mp
from pathlib import Path
import datetime

class WavNpyConverter:
    def __init__(self):
        pass

    def fetch_datapath(self, datasets_path, dataset_basename):
        for i in range(1, 100):
            dataset_fullname = "{basename}.{seq_number:0>2}".format(basename=dataset_basename, seq_number=i)
            dataset_path = Path(datasets_path) / dataset_fullname
            if not dataset_path.exists():
                dataset_path.mkdir()
                return dataset_path
        else:
            raise ValueError("dataset name {} is fully used".format(dataset_basename))

    def fetch_wavfiles(
        self,
        target_songs,
        readpath='songset/wav',
        sr=4096,
        songs_limit=10,
    ):
        wavfiles = list(map(lambda mvid: Path(readpath) / '{}.wav'.format(mvid), target_songs))
        if len(wavfiles) > songs_limit:
            wavfiles = wavfiles[:songs_limit]

        pool_args = [{
            'librosa': {
                'path': str(w),
                'sr': sr,
                'dtype': np.float32,
            },
        } for w in wavfiles]
        pool_results = []
        with mp.Pool() as pool:
            for _ in tqdm( pool.imap(self._wrap_load, pool_args), total=len(pool_args) ):
                pool_results.append(_)
        return pool_results

    def _wrap_load(self, kwargs):
        return librosa.core.load(**kwargs['librosa'])

    def constract_npyarray(self, waves, target_songs, memmap_path, length=8192, length_limit=5, duplication=4):
        pos = 0
        widths = tuple( map(lambda x: min( ( x[0].shape[-1] // length - 1 ) * duplication, length_limit ), waves) )

        npy_memmap = np.memmap(
            memmap_path,
            mode='w+',
            dtype=np.float32,
            shape=(sum(widths),1,length)
        )
        labels = []

        for array, mvid, w in zip(waves, target_songs, widths):
            for j in range(duplication):
                start_pos = length // duplication * j
                partial_count = (w-j-1) // duplication + 1
                end_pos = start_pos + length *partial_count
                npy_memmap[j:w:duplication, :] = \
                    array[0][start_pos:end_pos].reshape([partial_count, 1, length])

            labels.append([
                mvid,
                pos,
                pos + w
            ])
            pos += w

        return npy_memmap, labels

    def constract_score(self, labels):
        score = np.zeros([labels[-1][2]], dtype = np.float32)
        for song in labels:
            score[song[1]:song[2]] = Status.get_by_id(song[0]).score
        return score

    def constract_index(self, labels):
        index = np.zeros([labels[-1][2]], dtype = np.int32)
        for i, song in enumerate(labels):
            index[song[1]:song[2]] = i
        return index

    def constract_spectrogram(self, npyarray):
        spectro_shape = spectrogram(npyarray[0, :], window='hamming', mode='magnitude')[2].shape
        spectro = np.zeros([ npyarray.shape[0] ] + list(spectro_shape), dtype = np.float32)
        for i in range(npyarray.shape[0]):
            spectro[i, :] = np.log10( spectrogram(npyarray[i, :], window='hamming', mode='magnitude')[2] )
        return spectro

    def __call__(
        self,
        target_songs,
        readpath = 'songset/wav',
        datasets_path='datasets',
        dataset_basename=datetime.date.today().isoformat(),
        sr=4096,
        songs_limit=10,
        length_limit=100,
        length=8192,
        duplication=4,
    ):
        dataset_path = self.fetch_datapath(datasets_path, dataset_basename)
        wavdatas = self.fetch_wavfiles(target_songs, readpath=readpath, sr=sr, songs_limit=songs_limit)
        npyarray, labels = self.constract_npyarray(wavdatas, target_songs, dataset_path/'wav.memmap', length=length, length_limit=length_limit, duplication=duplication)

        with open(dataset_path/'label.json', 'w') as f:
            json.dump(labels, f, indent = 2)
        np.save(dataset_path/'score.npy',   self.constract_score(labels))
        np.save(dataset_path/'label.npy',   self.constract_index(labels))
        np.save(dataset_path/'spectro.npy', self.constract_spectrogram(npyarray))

        generation_params = {
            'samples': npyarray.shape[0],
            'length_per_sample': length,
            'sampling_rate': sr,
            'sample_songs': len(target_songs)
        }
        json.dump(generation_params, ( dataset_path/'info.json' ).open(mode='w'))

        print("Dataset has been successfully written in {path}".format(path=str( dataset_path )))
