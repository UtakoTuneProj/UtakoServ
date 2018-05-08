#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Analyzer: UtakoChainer core module
from utako.common_import import *
import chainer
import functools
import matplotlib.pyplot as plt

from utako.presenter.wave_loader import WaveLoader
from . import song_classifier as sc
from .pu_loss import pu_loss

class PUTagClassifierChain(sc.SongClassifierChain):

    # By R. Kiryo et al. (NIPS 2017)
    # GitHub: kiryor/nnPUlearning
    def error(self, x_data, y_data, train = True):
#        y = self(Variable(x_data))
#        t = Variable(y_data)
#
#        return pu_loss(y,t, prior = 0.1)

        y = self(Variable(x_data))
        t = Variable((y_data == 1).astype(cupy.int8))

        return F.sigmoid_cross_entropy(y,t)

class PUTagClassifier(sc.SongClassifier):
    def __init__(
        self,
        structure,
        modelclass = PUTagClassifierChain,
        *args,
        **kwargs
    ):
        super().__init__(
            structure,
            *args,
            modelclass = modelclass,
            **kwargs
        )

if __name__ == '__main__':
    main()
