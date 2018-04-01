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

from utako.presenter.wave_loader import WaveLoader
from . import song_classifier as sc

class SongAutoEncoderChain(sc.SongClassifierChain):

    def error(self, x_data, y_data, train = True):
        y = self(Variable(x_data))
        t = Variable(y_data)

        return F.mean_squared_error(y,t), y.data

class SongAutoEncoder(sc.SongClassifier):
    def __init__(
        self,
        structure,
        name = 'song_AE',
        n_epoch = 300,
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
    def set_data(self, train, y_train, test, y_test):
        if type(train) != np.ndarray or type(test) != np.ndarray :
            if os.path.isfile('train.npy') and os.path.isfile('test.npy'):
                train = np.load('train.npy')
                test = np.load('test.npy')
            else:
                self.x_train, self.x_test = WaveLoader().fetch(isTrain = True)

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

    def write_wave(self, wave, fname = None):
        if fname is None:
            fname = self.basename + '.wav'
        librosa.output.write_wav(fname, wave, sr=5513)

    def __call__(self, mode, mvid = None, modelfile = None):
        pass

    def examine(self, trial = None, write_wav = True):
        # trial: list/dict: list/dict for plot waveform and/or save wave if trial is None:
        train_loss, test_loss = super().examine()

        if trial is None:
            trial = {
                'train': self.x_train[334],
                'test' : self.x_test[893],
            }

        if type(trial) == dict:
            trial_keys, trial_values = zip(*trial.items())
            x_trial = np.array(trial_values)
        elif type(trial) in (list, np.ndarray):
            trial_keys = range(len(trial))
            x_trial = trial
        else:
            raise TypeError('SAE.examine only accepts dict, list or np.ndarray as trial. Not {}'.format(type(trial)))

        trial_batch, _ = self.get_batch(x_trial, x_trial)
        _, trial_predict_batch = self.challenge(trial_batch, trial_batch, isTrain = False)
        trial_predict = self.unify_batch(trial_predict_batch)

        for i, key in enumerate(trial_keys):
            waves = dict(
                teacher = x_trial[i],
                predict = trial_predict[i],
            )
            if self.isgui:
                self.visualize_wave(
                    waves = waves,
                    title = key,
                )

            if write_wav:
                for keyw in waves:
                    self.write_wave(
                        waves[keyw],
                        fname = '{}_{}_{}.wav'.format(self.basename, key, keyw),
                    )

        return train_loss, test_loss

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
