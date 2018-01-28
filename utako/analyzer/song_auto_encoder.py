#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Analyzer: UtakoChainer core module
from utako.common_import import *
import librosa
import librosa.display
from utako.presenter.wave_loader import WaveLoader
import matplotlib.pyplot as plt
import scipy.fftpack as fft

class SongAEModel(ChainList):
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
            h = F.relu(layer(h))
        o_layer = self.__getitem__(i+1)
        return o_layer(h)

    def reset_state(self):
        self.l[1].reset_state()
        self.l[-2].reset_state()

    def error(self, x_data, y_data, train = True):
        y = self(Variable(x_data))
        t = Variable(y_data)
        ret = y.data

        return F.mean_squared_error(y,t), ret

class SongAutoEncoder:
    def __init__(
        self,
        n_units,
        n_epoch = 300,
        batchsize = 50,
        x_train = None,
        x_test = None,
        isgpu = True
        isgui = True,
    ):
        self.n_epoch   = n_epoch
        self.batchsize = batchsize
        self.isgpu     = isgpu 
        self.isgui     = isgui 

        if self.isgpu:
            cuda.get_device(0).use()  # Make a specified GPU current
        self.set_model(n_units)
        self.set_data(x_train, x_test)

    def preprocess(self, x):
        return x

    def postprocess(self, x):
        return x

    def set_model(self, n_units):
        self.n_units = n_units
        self.in_size = n_units[0]
        self.model = SongAEModel(n_units = self.n_units)
        if self.isgpu:
            self.model.to_gpu()  # Copy the model to the GPU

        self.optimizer = optimizers.Adam()
        self.optimizer.setup(self.model)

    def set_data(self, train, test)
        if type(train) != np.ndarray or type(test) != np.ndarray :
            if os.path.isfile('train.npy') and os.path.isfile('test.npy'):
                self.x_train = np.load('train.npy')
                self.x_train = np.load('test.npy')
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
        random = False
        batchsize = self.batchsize
    ):
        if random:
            perm = np.random.permutation(len(data))
        else:
            perm = np.arange(len(data))

        data_size, length = data.shape
        tmp = [[ self.preprocess(
                data[perm[i:i+batchsize],
                j : j + in_size
            ]) for j in range(0, length, in_size)
            ] for i in range(0, data_size, batchsize)
        ]
        if self.gpu:
            batch = []
            for c1 in tmp:
                batch.append([])
                for c0 in c1: #時間方向
                    batch[-1].append(cuda.to_gpu(np.array(c0, dtype = np.float32)))
        else:
            batch = tmp

        return batch
    
    def unify_batch(self, batch):
        batch_count = len(batch)
        for i, batch_cell in enumerate(batch):
            batch_size, length = batch_cell[0].shape
            cell = np.zeros(0, batch_size)
            for time_cell in batch_cell:
                tmp = self.postprocess(time_cell)
                cell = np.append(cell, tmp, axis = 0)
            if i == 0:
                unified = cell
            else:
                unified = append(unified, cell, axis = 1)
        return unified

    def challenge(self, batch, isTrain = False):
        batch_count  = len(batch)
        sum_loss     = 0
        prediction   = [[] for i in range(batch_count))]
        for i in np.random.permutation(batch_count):
            batch_cell = batch[i]
            loss = 0
            # 勾配を初期化
            self.model.cleargrads()
            # initialize State
            self.model.reset_state()
            for time_cell in batch_cell:
                # 順伝播させて誤差と精度を算出
                moment_error, moment_prediction = self.model.error(time_cell, time_cell)
                if isTrain:
                    # 誤差逆伝播で勾配を計算
                    moment_error.backward()
                loss = moment_error.data
                prediction[i].append(moment_prediction)
            self.optimizer.update()
            sum_loss += loss

        return sum_loss, prediction

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

    def visualize_wave(self, *args, **kwargs):
        for i, s in enumerate(args):
            tmp = np.convolve(np.array(s), kernel, mode = 'valid')
            librosa.display.waveplot(s, label = str(i), alpha = 0.4)

        for key in kwargs:
            s = kwargs[key]
            librosa.display.waveplot(s, label = key, alpha = 0.4)
        plt.legend()
        plt.show()

    def write_wave(self, prefix = 'autoencode', *args, **kwargs):
        for i, s in enumerate(args):
            librosa.output.write_wav('{}.{}.wav'.format(prefix, i), s, 22050)
        for key in kwargs:
            s = kwargs[key]
            librosa.output.write_wav('{}.{}.wav'.format(prefix, key), s, 22050)

    def __call__(self, mode, mvid = None, modelfile = None):
        pass

    def learn(self):
        startTime = time.time()

        train_batch = self.get_batch(self.x_train)
        test_batch  = self.get_batch(self.x_test)
        train_loss  = []
        test_loss   = []

        # Learning loop
        for epoch in range(n_epoch):
            print('epoch', epoch + 1, flush = True)

            res, _ = self.challenge(train_batch, isTrain = True)
            # # 訓練データの誤差と、正解精度を表示
            print('train mean loss={}'.format(res))
            train_loss.append(res)

            # evaluation
            # テストデータで誤差と、正解精度を算出し汎化性能を確認

            res, _ = self.challenge(test_batch, isTrain = True)
            # # 訓練データの誤差と、正解精度を表示
            print('test mean loss={}'.format(res))
            test_loss.append(res)

            if epoch % 50 == 0:
                serializers.save_npz('Network/song_AE_{0:04d}.model'.format(epoch), model)

        elapsedTime = time.time() - startTime
        print('Total Time: {0}[min.]'.format(elapsedTime / 60))

        serializers.save_npz('Network/song_AE_final.model', model)

        if GUI:
            # 精度と誤差をグラフ描画
            # plt.plot(range(len(train_loss)), train_loss)
            self.visualize_loss(
                train = train_loss,
                test  = test_loss,
            )

            self.visualize_wave(
                teacher = self.x_test[3],
                predict = self.test_predict[3]
            )

        self.write_wave(
            teacher = self.x_test[3],
            predict = self.test_predict[3]
        )

        return train_loss, test_loss

    def examine(self):
        train_batch = self.get_batch(self.x_train)
        test_batch  = self.get_batch(self.x_test)

        res, train_predict_batch = self.challenge(train_batch, isTrain = True)
        # # 訓練データの誤差と、正解精度を表示
        print('train mean loss={}'.format(res))
        train_loss = res

        # evaluation
        # テストデータで誤差と、正解精度を算出し汎化性能を確認

        res, test_predict_batch = self.challenge(test_batch, isTrain = True)
        # # 訓練データの誤差と、正解精度を表示
        print('test mean loss={}'.format(res))
        test_loss = res

        train_predict = self.unify_batch(train_predict_batch)
        test_predict = self.unify_batch(test_predict_batch)

        if GUI:
            # 精度と誤差をグラフ描画
            # plt.plot(range(len(train_loss)), train_loss)
            self.visualize_loss(
                train = train_loss,
                test  = test_loss,
            )

            self.visualize_wave(
                teacher = self.x_test[3],
                predict = self.test_predict[3]
            )

        self.write_wave(
            teacher = self.x_test[3],
            predict = self.test_predict[3]
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
