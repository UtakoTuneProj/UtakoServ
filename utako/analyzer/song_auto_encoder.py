#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Analyzer: UtakoChainer core module
from utako.common_import import *
import librosa
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
    def __init__(self, isgpu = True):
        self.gpu = isgpu
        if isgpu:
            cuda.get_device(0).use()  # Make a specified GPU current

    def __call__(self, mode, mvid = None, modelfile = None):
        pass

    def learn(
        self,
        n_units = [
            8192,
            1024,
            128,
            16,
            128,
            1024,
            8192,
        ],
        n_epoch = 15,
        batchsize = 50,
        GUI = True,
        x_train = None,
        x_test = None,
    ):
        startTime = time.time()
        in_size = n_units[0]

        model = SongAEModel(n_units = n_units)
        if self.gpu:
            model.to_gpu()  # Copy the model to the GPU

        optimizer = optimizers.Adam()
        optimizer.setup(model)

        if type(x_train) != np.ndarray or type(x_test) != np.ndarray :
            x_train, x_test = WaveLoader().fetch(isTrain = True)
        y_train = x_train
        y_test = x_test

        N = len(x_train)
        N_train = N
        N_test = len(x_test)
        perm = np.arange(len(x_train) + len(x_test))
        # perm = np.random.permutation(N + N_test)

        train_loss = []
        test_loss = []

        perm = np.random.permutation(N_train)
        tmp = [[ fft.fft(
                x_train[perm[i:i+batchsize],
                j : j + in_size
            ]) for j in np.arange(0, len(x_train[0]), in_size)
            ] for i in np.arange(0, N_train, batchsize) ]
        if self.gpu:
            x_train_batch = []
            for c1 in tmp:
                x_train_batch.append([])
                for c0 in c1: #時間方向
                    x_train_batch[-1].append(cuda.to_gpu(np.array(c0, dtype = np.float32)))
        else:
            x_train_batch = tmp

        perm = np.random.permutation(N_test)
        tmp = [[ fft.fft(
                x_test[perm[i:i+batchsize],
                j : j + in_size
            ]) for j in np.arange(0, len(x_test[0]), in_size)
            ] for i in np.arange(0, N_test, batchsize) ]
        if self.gpu:
            x_test_batch = []
            for c1 in tmp:
                x_test_batch.append([])
                for c0 in c1: #時間方向
                    x_test_batch[-1].append(cuda.to_gpu(np.array(c0, dtype = np.float32)))
        else:
            x_test_batch = tmp

        # Learning loop
        for epoch in range(n_epoch):
            print('epoch', epoch + 1, flush = True)

            # training
            # N個の順番をランダムに並び替える
            # sum_accuracy = [0 for i in range(N_model)]
            sum_loss     = 0
            # 0〜Nまでのデータをバッチサイズごとに使って学習
            for batch_cell in x_train_batch:
                # 勾配を初期化
                loss = 0
                model.cleargrads()
                # initialize State
                model.reset_state()
                for time_cell in batch_cell:
                    # 順伝播させて誤差と精度を算出
                    tmp, _ = model.error(time_cell, time_cell)
                    loss += tmp
                # 誤差逆伝播で勾配を計算
                loss.backward()
                optimizer.update()
                sum_loss += loss.data * batchsize * in_size

            # # 訓練データの誤差と、正解精度を表示
            print('train mean loss={}'.format(sum_loss / N))
            train_loss.append(sum_loss / N)

            # evaluation
            # テストデータで誤差と、正解精度を算出し汎化性能を確認
            sum_loss  = 0

            for batch_cell in x_test_batch:
                # 勾配を初期化
                loss = 0
                if epoch == n_epoch - 1:
                    test_data = []
                model.cleargrads()
                # initialize State
                model.reset_state()
                for time_cell in batch_cell:
                    # 順伝播させて誤差と精度を算出
                    tmp, op = model.error(time_cell, time_cell)
                    loss += tmp
                    if epoch == n_epoch - 1:
                        op = cuda.to_cpu(op)
                        test_data.append(op)
                sum_loss += loss.data * batchsize * in_size

            # テストデータでの誤差と、正解精度を表示
            print('test mean loss={}'.format(sum_loss / N_test))
            test_loss.append(sum_loss / N_test)

        elapsedTime = time.time() - startTime
        print('Total Time: {0}[min.]'.format(elapsedTime / 60))

        serializers.save_npz('Network/song_AE.model', model)

        if GUI:
            # 精度と誤差をグラフ描画
            # plt.plot(range(len(train_loss)), train_loss)
            kernel = np.ones(5)/5
            test_loss = np.convolve(np.array(test_loss), kernel, mode = 'valid')
            plt.plot(range(len(test_loss)), test_loss, label = 'MSE')
            plt.legend()
            plt.yscale('log')
            plt.show()

            if self.gpu:
                y_test = cuda.to_cpu(y_test)
            y_got = np.zeros((batchsize, 0))
            for cell in test_data:
                y_got = np.append(y_got, fft.ifft(cell), axis = 1)

            plt.plot(range(len(y_test[0])), y_test[0], label = 'Ans.')
            plt.plot(range(len(y_test[0])), test_data[0], label = 'Auto Encode')
            plt.legend()
            plt.show()

        librosa.output.write_wav('original.wav', y_test[0], 22050)
        librosa.output.write_wav('coded.wav', test_data[0], 22050)

#    def examine(modelpath, n_units = 200, layer = 20):
#        f = sql.fetch(isTrain = True)
#        x = np.array(f[0][args.testgroup], dtype = np.float32)
#        y = 100 * np.log10(np.array(f[1][args.testgroup], dtype = np.float32))
#
#        N_test = len(y)
#
#        model = ChartModel(n_units = n_units, layer = layer)
#        serializers.load_npz(modelpath, model)
#        e, l = model.error(x, y.reshape((len(y), 1)), train = False)
#
#        if GUI:
#            index = np.argsort(y, axis = 0)
#            y = y[index[:,0],:]
#            l = l[index[:,0],:]
#            plt.plot(y, range(N_test), label = 'Ans.')
#            plt.plot(l, range(N_test), label = 'Exam.')
#            plt.legend()
#            plt.show()
#
#            plt.hist(l-y, bins = 50)
#            plt.show()
#
#        return e.data, np.mean(l-y), np.std(l-y)
#
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
