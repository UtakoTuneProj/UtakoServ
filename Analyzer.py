# coding: utf-8
# Analyzer: UtakoChainer core module

import sys
import numpy as np
from chainer import cuda, Variable, optimizers, Chain, ChainList, serializers
import chainer.functions  as F
import chainer.links as L
try:
    import matplotlib.pyplot as plt
    GUI = True
except:
    GUI = False

import ServCore as core
import ChartInitializer as chinit

class ChartModel(ChainList):
    def __init__(self, in_layer = 109, n_units = 50, layer = 4):
        l = [L.Linear(in_layer, n_units)]
        l.extend([L.Linear(n_units, n_units) for x in range(layer - 2)])
        l.append(L.Linear(n_units, 1))
        super().__init__(*l)

    def __call__(self, x):
        h = x
        for i in range(self.__len__() - 1):
            layer = self.__getitem__(i)
            h = F.relu(layer(h))
        o_layer = self.__getitem__(i+1)
        return o_layer(h)

    def error(self, x_data, y_data, train = True):
        y = self(Variable(x_data))
        t = Variable(y_data)
        if not train:
            ret = y.data
        else:
            ret = None

        return F.mean_squared_error(y,t), ret

def learn():

    batchsize = 500
    n_epoch = 3000

    N_model = len(config)
    model = [None for i in range(N_model)]
    optimizer = [None for i in range(N_model)]

    for i,c in enumerate(config):
        model[i] = ChartModel(n_units = c[0], layer = c[1])
        optimizer[i] = optimizers.Adam()
        optimizer[i].setup(model[i])

    # train_loss = [[] for i in range(5)]
    # train_acc  = [[] for i in range(5)]
    test_loss = [[] for i in range(N_model)]
    test_acc  = [[] for i in range(N_model)]

    test_data = [[] for i in range(N_model)]

    lfile = core.InitChartfile()
    x_dump = np.array(lfile.x, dtype = np.float32)
    y_dump = 100 * np.log10(np.array(lfile.vocaran, dtype = np.float32))

    N = len(x_dump) - N_test
    perm = np.arange(len(x_dump))
    # perm = np.random.permutation(N + N_test)

    x_train = x_dump[perm[:-N_test]]
    y_train = y_dump[perm[:-N_test]]
    x_test = x_dump[perm[-N_test:]]
    y_test = y_dump[perm[-N_test:]]

    # Learning loop
    for epoch in range(n_epoch):
        print('epoch', epoch + 1, flush = True)

        # training
        # N個の順番をランダムに並び替える
        perm = np.random.permutation(N)
        # sum_accuracy = [0 for i in range(N_model)]
        sum_loss     = [0 for i in range(N_model)]
        # 0〜Nまでのデータをバッチサイズごとに使って学習
        for i in range(0, N, batchsize):
            x_batch = x_train[perm[i:i+batchsize]]
            y_batch = y_train[perm[i:i+batchsize]]

            for j in range(N_model):
                # 勾配を初期化
                optimizer[j].zero_grads()
                # 順伝播させて誤差と精度を算出
                loss, _ = model[j].error(x_batch, y_batch.reshape((len(y_batch),1)))
                # 誤差逆伝播で勾配を計算
                loss.backward()
                optimizer[j].update()
                # sum_loss[j] += loss.data * batchsize

        # # 訓練データの誤差と、正解精度を表示
        # print('train mean loss={}'.format(sum_loss / N))
        # train_loss.append(sum_loss / N)

        # evaluation
        # テストデータで誤差と、正解精度を算出し汎化性能を確認
        sum_loss  = [0 for i in range(N_model)]
        test_data = [[] for i in range(N_model)]

        for i in range(0, N_test):
            x_batch = x_test[i:i+1]
            y_batch = y_test[i:i+1]

            for j in range(N_model):
                # 順伝播させて誤差と精度を算出
                loss, op = model[j].error(x_batch, y_batch.reshape((len(y_batch),1)), train = False)
                sum_loss[j] += loss.data
                if epoch == n_epoch - 1:
                    test_data[j].append(list(op.reshape(len(op))))

        for j in range(N_model):
            # テストデータでの誤差と、正解精度を表示
            print('test{0} mean loss={1}'.format(j, sum_loss[j] / N_test))
            test_loss[j].append(sum_loss[j] / N_test)

    for i in range(N_model):
        serializers.save_npz('Network/chart'+str(i)+'.model', model[i])

    if GUI:
        # 精度と誤差をグラフ描画
        # plt.plot(range(len(train_loss)), train_loss)
        kernel = np.ones(5)/5
        for i in range(N_model):
            test_loss[i] = np.convolve(np.array(test_loss[i]), kernel, mode = 'valid')
            plt.plot(range(len(test_loss[i])), test_loss[i], label = config[i])
        plt.legend()
        plt.yscale('log')
        plt.show()

        test_data.insert(0,list(y_test))
        dump = list(zip(*test_data))
        dump.sort()
        plt_data = list(zip(*dump))

        plt.plot(plt_data[0], range(N_test), label = 'Ans.')
        for i in range(N_model):
            plt.plot(plt_data[i+1],range(N_test), label = config[i])
        plt.legend()
        plt.show()

def model_test():
    N_model = len(config)
    model = [None for i in range(N_model)]

    lfile = core.InitChartfile()
    x_dump = np.array(lfile.x[-N_test:], dtype = np.float32)
    y_dump = 100 * np.log10(np.array(lfile.vocaran[-N_test:], dtype = np.float32))

    N = len(x_dump) - N_test
    perm = np.arange(len(x_dump))

    y = [None for i in range(N_model + 1)]
    e = [None for i in range(N_model)]
    x = x_dump[perm[-N_test:]]
    y[0] = y_dump[perm[-N_test:]]

    for i in range(N_model):
        model[i] = ChartModel(n_units = config[i][0], layer = config[i][1])
        serializers.load_npz('Network/chart'+str(i)+'.model', model[i])
        e, y[i+1] = model[i].error(x, y[0].reshape((len(y[0]), 1)), train = False)
        print(e.data, flush = True)

    y = [list(z.reshape(len(z))) for z in y]
    y = list(zip(*y))
    y.sort()
    y = list(zip(*y))

    plt.plot(y[0], range(N_test), label = 'Ans.')
    for i in range(N_model):
        plt.plot(y[i+1], range(N_test), label = config[i])
    plt.legend()
    plt.show()

def analyze(mvid):
    model24 = ChartModel(n_units = 600, layer = 7)
    serializers.load_npz('Network/chart24h.model', model24)
    [status, x, y] = chinit.normalizer(mvid, on_prog = True)
    if status == 24:
        y = model24(np.array(x, dtype = np.float32).reshape((1, len(x))))
        return y
    else:
        return None

def main():
    model_test()

if __name__ == '__main__':
    N_test = 500
    config = [[600,7],
              [600,7],
              [600,7]]
    main()
