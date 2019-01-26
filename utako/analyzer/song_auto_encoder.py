#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Analyzer: UtakoChainer core module
from utako.common_import import *
import chainer
import functools
import librosa
import librosa.display
import matplotlib.pyplot as plt
import scipy.fftpack as fft

from . import song_classifier as sc

class SongAutoEncoderChain(sc.SongClassifierChain):

    def error(self, x_data, y_data, train = True):
        y = self(Variable(x_data))
        t = Variable(y_data)

        return F.mean_squared_error(y,t)

class SongAutoEncoder(sc.SongClassifier):
    def __init__(
        self,
        structure,
        name = 'song_AE',
        n_epoch = 300,
        save_epoch = 10,
        batchsize = 50,
        x_train = None,
        x_test = None,
        isgpu = True,
        isgui = True,
        preprocess = lambda x: x,
        postprocess = lambda x: x,
        modelclass = SongAutoEncoderChain
    ):
        super().__init__(
            structure,
            name = name,
            n_epoch = n_epoch,
            save_epoch = save_epoch,
            batchsize = batchsize,
            x_train = x_train,
            y_train = x_train,
            x_test = x_test,
            y_test = x_test,
            isgpu = isgpu,
            isgui = isgui,
            preprocess = preprocess,
            postprocess = postprocess,
            modelclass = modelclass,
        )
    
    def set_model(self, modelclass, **kwargs):
        self.predictor = modelclass(structure = self.structure, **kwargs)
        self.model = L.Classifier(
            self.predictor,
            lossfun=F.mean_squared_error,
            accfun=F.mean_absolute_error,
        )
        if self.isgpu:
            self.model.to_gpu()

        self.optimizer = optimizers.AdaGrad()
        self.optimizer.setup(self.model)

    def set_data(self, train, y_train, test, y_test):
        if type(train) != np.ndarray or type(test) != np.ndarray :
            raise TypeError('train, test must be np.ndarray')

        super().set_data(train, train, test, test)

    def visualize_wave(self, waves, title = None, **kwargs):
        if type(waves) is dict:
            for key in waves:
                s = waves[key]
                librosa.display.waveplot(s, label = key, alpha = 0.4, **kwargs)
        elif type(waves) in (list, np.ndarray):
            for i, s in enumerate(args):
                librosa.display.waveplot(s, label = str(i), alpha = 0.4, **kwargs)
        else:
            raise TypeError('SAE.visualize_wave only accepts dict, list or np.ndarray as waves. Not {}'.format(type(waves)))

        plt.title(title)
        plt.legend()
        plt.show()

    def extend_trainer(self, trainer):
        super().extend_trainer(trainer)
        trainer.extend(write_wave(self.predictor, self.test_iter.next(), self.basename, isgpu=self.isgpu))

def write_wave(model, waves, basename, isgpu=False):
    @chainer.training.make_extension(trigger=(10, 'epoch'))
    def write_wave(trainer):
        for i, w in enumerate(waves):
            x, y = map(lambda x: x.reshape(1,1,-1), w)
            if isgpu:
                x = chainer.cuda.to_gpu(x)
            p = model(x)
            if isgpu:
                p.to_cpu()
            fname = basename + '.{}.predict.wav'.format(i)
            librosa.output.write_wav(fname, p.data.reshape(-1), sr=5513)
            fname = basename + '.{}.teacher.wav'.format(i)
            librosa.output.write_wav(fname, y.reshape(-1), sr=5513)

    return write_wave

#    def analyze():
#        model = ChartModel(n_units = n_units, layer = layer)
#        serializers.load_npz(args.modelfile[0], model)
#
#        [x, _] = sql.fetch(mvid = mvid)
#        return model(np.array(x, dtype = np.float32).reshape((1, len(x[0][0])))).data[0][0]
#
#    def main():
#        if args.mode in ['l', 'learn']:
#            learn()
#        elif args.mode in ['x', 'examine']:
#            for mp in args.modelfile:
#                print(examine(modelpath = mp))
#        else:
#            print(analyze(args.mvid))


if __name__ == '__main__':
    main()
