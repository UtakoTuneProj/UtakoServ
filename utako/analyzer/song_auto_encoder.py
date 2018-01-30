#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Analyzer: UtakoChainer core module
from utako.common_import import *
import librosa
import librosa.display
from utako.presenter.wave_loader import WaveLoader
import matplotlib.pyplot as plt
import scipy.fftpack as fft

class SongAutoEncoderSigmoidModel(ChainList):
    def __init__(self, n_units):
        self.l = [
            L.Linear(*n_units[i:i+2])
            for i in range(len(n_units) - 1)
        ]
        self.l[1] = L.LSTM(*n_units[1:3])
        self.l[-2] = L.LSTM(*n_units[-3:-1])
        super().__init__(*self.l)

    def __call__(self, x):
        h = -x
        for i in range(self.__len__() - 1):
            layer = self.__getitem__(i)
            h = F.sigmoid(layer(h))
        o_layer = self.__getitem__(i+1)
        return o_layer(h)

    def reset_state(self):
        self.l[1].reset_state()
        self.l[-2].reset_state()

    def error(self, x_data, y_data, train = True):
        y = self(Variable(x_data))
        t = Variable(y_data)

        return F.mean_squared_error(y,t), y.data

class SongAutoEncoderReluModel(SongAutoEncoderSigmoidModel):
    def __call__(self, x):
        h = -x
        for i in range(self.__len__() - 1):
            layer = self.__getitem__(i)
            h = F.relu(layer(h))
        o_layer = self.__getitem__(i+1)
        return o_layer(h)

class SongAutoEncoder:
    def __init__(
        self,
        n_units,
        name = 'song_AE',
        n_epoch = 300,
        batchsize = 50,
        x_train = None,
        x_test = None,
        isgpu = True,
        isgui = True,
        preprocess = lambda x: x,
        postprocess = lambda x: x,
        modelclass = SongAutoEncoderSigmoidModel
    ):
        self.n_epoch    = n_epoch
        self.name       = name
        self.batchsize  = batchsize
        self.isgpu      = isgpu 
        self.isgui      = isgui 
        self.preprocess = preprocess
        self.postprocess= postprocess
        self.basename  = 'result/{}'.format(name)

        if self.isgpu:
            cuda.get_device(0).use()  # Make a specified GPU current
        self.set_model(n_units, modelclass, self.basename+'.model')
        self.set_data(x_train, x_test)

    def set_model(self, n_units, modelclass, modelfile = None):
        self.n_units = n_units
        self.in_size = n_units[0]
        self.model = modelclass(n_units = self.n_units)

        if (modelfile is not None) and (os.path.isfile(modelfile)):
            serializers.load_npz(modelfile, self.model)

        if self.isgpu:
            self.model.to_gpu()  # Copy the model to the GPU

        self.optimizer = optimizers.Adam()
        self.optimizer.setup(self.model)

    def set_data(self, train, test):
        if type(train) != np.ndarray or type(test) != np.ndarray :
            if os.path.isfile('train.npy') and os.path.isfile('test.npy'):
                self.x_train = np.load('train.npy')
                self.x_test = np.load('test.npy')
            else:
                self.x_train, self.x_test = WaveLoader().fetch(isTrain = True)
        else:
            self.x_train = train
            self.x_test  = test

        self.N_train = len(self.x_train)
        self.N_test  = len(self.x_test)

    def get_batch(
        self,
        data,
        random = False,
        batchsize = None,
    ):
        data_size, length = data.shape
        if batchsize is None:
            batchsize = self.batchsize

        if data_size % batchsize != 0:
            data = np.append(
                data,
                data[np.random.permutation(
                    batchsize - data_size % batchsize
            ) % data_size], axis = 0)

        if self.isgpu:
            data = cuda.to_gpu(data)

        data_size, length = data.shape
        if random:
            cupy.random.shuffle(data)
        batch = data.reshape(
            data_size // batchsize,
            batchsize,
            length // self.in_size,
            self.in_size
        ).transpose(0,2,1,3)

        return batch 
    
    def unify_batch(self, batch):
        batch_count, time_count, batchsize, timesize = batch.shape
        res = batch.transpose(0,2,1,3).reshape(batch_count * batchsize, time_count * timesize)
        if self.isgpu:
            res = cuda.to_cpu(res)
        return res

    def challenge(self, batch, isTrain = False):
        batch_count, time_count, batchsize, timesize = batch.shape
        prediction   = cupy.zeros(batch.shape)
        sum_loss     = 0
        perm = cupy.arange(batch_count)
        if isTrain:
            cupy.random.shuffle(perm)
        for i in perm:
            loss = 0
            # initialize State
            self.model.reset_state()
            for j in cupy.arange(time_count):
                # 勾配を初期化
                self.model.cleargrads()
                # 順伝播させて誤差と精度を算出
                moment_error, moment_prediction = self.model.error(batch[i,j,:,:], batch[i,j,:,:])
                if isTrain:
                    # 誤差逆伝播で勾配を計算
                    moment_error.backward()
                    self.optimizer.update()
                loss += moment_error.data
                prediction[i, j, :, :] = moment_prediction
            sum_loss += loss

        return float(sum_loss), prediction

    def visualize_loss(self, *args, **kwargs):
        kernel = np.ones(5)/5

        for i, s in enumerate(args):
            tmp = np.convolve(np.array(s), kernel, mode = 'valid')
            plt.plot(range(len(tmp)), tmp, label = str(i))
        for key in kwargs:
            s = kwargs[key]
            tmp = np.convolve(np.array(s), kernel, mode = 'valid')
            plt.plot(range(len(tmp)), tmp, label = key)
        plt.legend()
        plt.yscale('log')
        plt.show()

    def visualize_wave(self, waves, **kwargs):
        if type(waves) is dict:
            for key in waves:
                s = waves[key]
                librosa.display.waveplot(s, label = key, alpha = 0.4, **kwargs)
        elif type(waves) in (list, np.ndarray)
            for i, s in enumerate(args):
                librosa.display.waveplot(s, label = str(i), alpha = 0.4, **kwargs)
        else:
            raise TypeError('SAE.visualize_wave only accepts dict, list or np.ndarray as waves. Not {}'.format(type(waves)))

        plt.legend()
        plt.show()

    def write_wave(self, wave, fname = None):
        if fname is None:
            fname = self.basename + '.wav'
        librosa.output.write_wav(fname, wave, sr=22050)

    def __call__(self, mode, mvid = None, modelfile = None):
        pass

    def learn(self):
        startTime = time.time()

        train_batch = self.get_batch(self.x_train)
        test_batch  = self.get_batch(self.x_test)
        train_loss  = []
        test_loss   = []

        # Learning loop
        for epoch in range(self.n_epoch):
            print('epoch', epoch + 1, flush = True)

            res, _ = self.challenge(train_batch, isTrain = True)
            # # 訓練データの誤差と、正解精度を表示
            print('train mean loss={}'.format(res))
            train_loss.append(res)

            # evaluation
            # テストデータで誤差と、正解精度を算出し汎化性能を確認

            res, _ = self.challenge(test_batch, isTrain = False)
            # # 訓練データの誤差と、正解精度を表示
            print('test mean loss={}'.format(res))
            test_loss.append(res)

            if epoch % 50 == 0:
                serializers.save_npz('{0}_{1:04d}.model'.format(self.basename, epoch), self.model)

        elapsedTime = time.time() - startTime
        print('Total Time: {0}[min.]'.format(elapsedTime / 60))

        serializers.save_npz('{0}_{1:04d}.model'.format(self.basename, epoch), self.model)

        _, train_predict_batch = self.challenge(train_batch, isTrain = False)
        _, test_predict_batch = self.challenge(test_batch, isTrain = False)
        train_predict = self.unify_batch(train_predict_batch)
        test_predict = self.unify_batch(test_predict_batch)


        if self.isgui: 
            # 精度と誤差をグラフ描画
            # plt.plot(range(len(train_loss)), train_loss)
            self.visualize_loss(
                train = train_loss,
                test  = test_loss,
            )

            self.visualize_wave(
                waves = dict(
                    teacher = self.x_test[3],
                    predict = test_predict[3]
                )
            )


        self.write_wave(self.x_test[3], fname = self.basename + '_teacher.wav')
        self.write_wave(self.test_predict[3], fname = self.basename + '_predict.wav')

        with open('{}.json'.format(self.basename), 'w') as f:
            json.dump([train_loss, test_loss], f)

        return train_loss, test_loss

    def examine(self, trial = None):
        # trial: list/dict: list/dict for plot waveform and/or save wave
        if trial is None:
            trial = {
                'train': self.x_trial[3]
                'test' : self.x_test[3]
            }
        if type(trial) == dict:
            trial_keys, trial_values = zip(*trial.items())
            x_trial = np.array(trial_values)
        else type(trial) in (list, np.ndarray):
            trial_keys = range(len(trial))
            x_trial = trial
        else:
            raise TypeError('SAE.examine only accepts dict, list or np.ndarray as trial. Not {}'.format(type(trial)))

        train_batch = self.get_batch(self.x_train)
        test_batch  = self.get_batch(self.x_test)
        trial_batch = self.get_batch(x_trial)

        train_loss, _ = self.challenge(train_batch, isTrain = False)
        test_loss, _ = self.challenge(test_batch, isTrain = False)
        _, trial_predict_batch = self.challenge(trial_batch, isTrain = False)
        print('train mean loss={}'.format(train_loss))
        print('test mean loss={}'.format(test_loss))

        trial_predict = self.unify_batch(trial_predict_batch)

        for i, key in enumerate(trial_keys):
            waves = dict(
                teacher = self.x_trial[i],
                predict = trial_predict[i],
            )
            if self.isgui:
                self.visualize_wave(
                    waves = waves
                    title = key,
                )

            for keyw in waves:
                self.write_wave(
                    self.x_test[waves],
                    fname = '{}_{}.wav'.format(self.basename, keyw)
                )

        return train_loss, test_loss

#    def analyze(mvid, n_units = 200, layer = 20):
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
