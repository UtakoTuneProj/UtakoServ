#!/usr/bin/env python3

from utako.common_import import *
from utako.exception.index_core_not_found_exception import IndexCoreNotFoundException
from scipy.stats import multivariate_normal as mvnm

def main(encoded_all, song_list, limit = 0.05):
    ret = np.zeros(( len(song_list), encoded_all.shape[-1] ))
    for i,s in enumerate(song_list):
        encoded = encoded_all[s[1]:s[2]]
        mean = np.average(encoded, axis=0)
        cov = np.cov(encoded.T)
        isnt_err = (mvnm.pdf(encoded, mean = mean, cov = cov, allow_singular = True) > limit)
        if not np.any(isnt_err):
            raise IndexCoreNotFoundException(s[0])
        clipped_mean = np.average(encoded[isnt_err], axis=0)
        ret[i,...] += clipped_mean
    return ret

