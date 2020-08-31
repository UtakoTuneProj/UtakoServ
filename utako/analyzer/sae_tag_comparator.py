#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utako.common_import import *
from utako.analyzer.song_auto_encoder import SongAutoEncoder
from utako.model.idtag import Idtag
from scipy import stats
import peewee
import gc

class SaeTagComparator:
    def __init__(self, conf_file = None, **kwargs):
        if conf_file is None:
            conf_file = 'conf/sae.yaml'
        with open(conf_file) as f:
            structure = yaml.safe_load(f)
        self.sae = SongAutoEncoder(structure, **kwargs)

    def __call__(self, trial, song_partition_file='train.json'):
        with open(song_partition_file) as f:
            song_partition = json.load(f)

        song_data = self.get_encoded(trial)
#       song_data = self.avg_per_song(encoded, song_partition)
        valid_tags = self.get_tags()

        return self.compare(song_data, song_partition, valid_tags)

    def get_encoded(self, trial):
        trial_batch = self.sae.get_batch(trial)
        for i, _ in enumerate(trial_batch):
            for j, __ in enumerate(_):
                with chainer.no_backprop_mode():
                    trial_encoded_cell = self.sae.model.encode(trial_batch[i, j, :, :, :]).data
                if i == 0 and j == 0:
                    trial_encoded_batch = cupy.zeros(
                        (len(trial_batch), len(_))
                        + trial_encoded_cell.shape
                    )
                trial_encoded_batch[i,j,:,:,:] = trial_encoded_cell

        trial_encoded = self.sae.unify_batch(trial_encoded_batch)
        return trial_encoded

    def avg_per_song(self, encoded, song_partition):
        ret = np.zeros((0, encoded.shape[-1]))
        for song in song_partition:
            song_data = np.average(encoded[song[1]:song[2], :], axis = 0)
            ret = np.append(ret, song_data.reshape(1,-1), axis = 0)

        return ret

    def get_tags(self, min_limit = 5):
        query = Idtag.select(
                    Idtag.tagname,
                ).group_by(
                    Idtag.tagname
                ).having(
                    peewee.fn.COUNT(1) > min_limit
                )
        return [t.tagname for t in query]

    def get_tagged_ids(self, tagname):
        query = Idtag.select(
                    Idtag.status_id
                ).where(
                    Idtag.tagname == tagname
                )
        return [t.id for t in query]

    def split_tagged(self, song_data, song_partition, tag):
        tagged = np.zeros(( 0, song_data.shape[-1] ))
        untagged = np.zeros(( 0, song_data.shape[-1] ))
        tagged_mvs = self.get_tagged_ids(tag)

        for i, song in enumerate(song_partition):
            if song[0].split('.')[0] in tagged_mvs:
                tagged = np.append(tagged, song_data[song[1]:song[2],:], axis = 0)
            else:
                untagged = np.append(untagged, song_data[song[1]:song[2],:], axis = 0)

        return tagged, untagged

    def compare(self, song_data, song_partition, valid_tags):
        result = []
        pb = ProgressBar()
        print('comparing...')
        for tag in pb( valid_tags ):

            tagged_mvs = self.get_tagged_ids(tag)
            tagged_set = set(tagged_mvs)
            song_ids = list(zip(*song_partition))[0]
            fetched_set = set(map(lambda x: x.split('.')[0], song_ids ))
            if len(tagged_set & fetched_set) == 0:
                continue
            else:
                tagged, untagged = self.split_tagged(song_data, song_partition, tag)

            if tagged.shape[0] < 2 or untagged.shape[0] < 2:
                continue
            else:
                tmp = stats.ttest_ind(tagged, untagged, equal_var = False)
                result.append(( tag, tagged.shape[0], untagged.shape[0], tmp ))

        return result

    def extract(self, result, pvalue_limit = 0.05):
        out = {}
        for res in result:
            for i in range(len(res[3].pvalue)):
                if res[3].pvalue[i] > pvalue_limit:
                    continue

                cell = {
                    'tagname': res[0],
                    'pvalue': res[3].pvalue[i],
                    'statistic': res[3].statistic[i],
                }
                if i not in out:
                    out[i] = [cell]
                else:
                    out[i].append(cell)

        return out
