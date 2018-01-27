#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Analyzer: UtakoChainer core module
from utako.common_import import *
import librosa
from utako.presenter.wave_loader import WaveLoader
import matplotlib.pyplot as plt

class SongAEModel(ChainList):
    def __init__(self, n_units):
        l = [
            L.Linear(*n_units[i:i+2])
            for i in range(len(n_units) - 1)
        ]
        super().__init__(*l)

    def __call__(self, x):
        h = -x
        for i in range(self.__len__() - 1):
            layer = self.__getitem__(i)
            h = F.relu(layer(h))
        o_layer = self.__getitem__(i+1)
        return o_layer(h)

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
            220500,
        #   17000,
        #   1300,
            100,
        #   1300,
        #   17000,
            220500
        ],
        n_epoch = 15,
        batchsize = 50,
        GUI = True,
        x_train = None,
        x_test = None,
    ):
        startTime = time.time()

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
        N_test = len(x_test)
        perm = np.arange(len(x_train) + len(x_test))
        # perm = np.random.permutation(N + N_test)

        # train_loss = [[] for i in range(5)]
        # train_acc  = [[] for i in range(5)]
        test_loss = []
        test_acc  = []

        if self.gpu:
            x_train = cuda.to_gpu(x_train)
            x_test  = cuda.to_gpu(x_test)
            y_train = cuda.to_gpu(y_train)
            y_test  = cuda.to_gpu(y_test)

        # Learning loop
        for epoch in range(n_epoch):
            print('epoch', epoch + 1, flush = True)

            # training
            # N個の順番をランダムに並び替える
            perm = np.random.permutation(N)
            # sum_accuracy = [0 for i in range(N_model)]
            sum_loss     = 0
            # 0〜Nまでのデータをバッチサイズごとに使って学習
            for i in range(0, N, batchsize):
                x_batch = x_train[perm[i:i+batchsize]]
                y_batch = y_train[perm[i:i+batchsize]]

                # 勾配を初期化
                model.cleargrads()
                # 順伝播させて誤差と精度を算出
                loss, _ = model.error(x_batch, y_batch)
                # 誤差逆伝播で勾配を計算
                loss.backward()
                optimizer.update()
                # sum_loss += loss.data * batchsize

            # # 訓練データの誤差と、正解精度を表示
            # print('train mean loss={}'.format(sum_loss / N))
            # train_loss.append(sum_loss / N)

            # evaluation
            # テストデータで誤差と、正解精度を算出し汎化性能を確認
            sum_loss  = 0

            for i in range(0, N_test, batchsize):
                x_batch = x_test[i:i+batchsize]
                y_batch = y_test[i:i+batchsize]
                size = len(y_batch)

                # 順伝播させて誤差と精度を算出
                loss, op = model.error(
                    x_batch, y_batch, train = False
                )
                sum_loss += loss.data * size
                if epoch == n_epoch - 1:
                    op = cuda.to_cpu(op)
                    test_data = op

            # テストデータでの誤差と、正解精度を表示
            print('mean loss={}'.format(sum_loss / N_test))
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

            plt.plot(range(N_test), y_test, label = 'Ans.')
            plt.plot(range(N_test), test_data, label = 'Auto Encode')
            plt.legend()
            plt.show()

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
