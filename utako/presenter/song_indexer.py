#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *
from utako.analyzer.song_classifier import SongClassifierChain
from utako.analyzer import song_classifier_postprocess as scpost
from .nico_downloader import NicoDownloader as NDL
import librosa

class SongIndexer:
    def __init__(self, structure):
        self.model = SongClassifierChain(structure)
    def __call__(self, mvid, sr = 5513, length = 8192, retries = 5):
        wav_formatted = self.fetch_npyarray(mvid, sr, length, retries)
        encoded_raw = self.model.encode(wav_formatted)
        score = scpost.main(
            encoded_raw.data,
            [ [mvid, 0, wav_formatted.shape[0]] ]
        )
        return score.reshape(-1)
    def fetch_npyarray(self, mvid, sr, length, retries = 5, cleanup = True):
        NDL()(mvid, retries = retries, dl_timeout_sec=200, use_partial=True, force=True)
        wav_raw = librosa.core.load(
            path = 'tmp/wav/{}.wav'.format(mvid),
            sr = sr,
            dtype = np.float32
        )
        sample_count = wav_raw[0].shape[-1] // length
        wav_formatted = wav_raw[0][:length*sample_count].reshape(sample_count, 1, length)
        if cleanup:
            os.remove('tmp/wav/{}.wav'.format(mvid))
            os.remove('tmp/mp4/{}.mp4'.format(mvid))
        return wav_formatted

