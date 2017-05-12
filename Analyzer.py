# coding: utf-8
# Analyzer: UtakoChainer core module
if __name__ == '__main__':
    print("importing modules...")

import sys
import time
import argparse

from progressbar import ProgressBar
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

if __name__ == '__main__':
    print('imported modules')

class ChartModel(ChainList):
    def __init__(self, in_layer = 96, n_units = 50, layer = 4):
        l = [L.Linear(in_layer, n_units)]
        if layer > 2:
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
        ret = y.data

        return F.mean_squared_error(y,t), ret

def learn():
    startTime = time.time()

    model = [None for i in range(N_model)]
    optimizer = [None for i in range(N_model)]

    for i,c in enumerate(config):
        model[i] = ChartModel(n_units = c[0], layer = c[1])
        if args.gpu:
            model[i].to_gpu()  # Copy the model to the GPU

        optimizer[i] = optimizers.Adam()
        optimizer[i].setup(model[i])

    db = core.DataBase('test')
    qtbl = core.QueueTable(db)
    ctbl = core.ChartTable(db)

    rawCharts = []
    shapedInputs = []
    shapedOutputs = []

    pb = ProgressBar(0, 20)
    print("Fetching from database...")
    for i in range(20):
        rawCharts.append(db.get(
            'select chart.* from chart join status using(ID)' +
            'where status.analyzeGroup = ' + str(i) + ' and isComplete = 1'
        ))
        pb.update(i+1)
    print("Fetch completed. Got data size is "\
        + str(sum([len(rawCharts[i]) for i in range(20)])))

    mvid = None
    for rawGroup in rawCharts:
        shapedInputs.append([])
        shapedOutputs.append([])
        for cell in rawGroup:
            if mvid != cell[0]:
                shapedInputs[-1].append([])
                mvid = cell[0]

            if cell[1] != 24:
                shapedInputs[-1][-1].extend(cell[2:])
            else:
                view = cell[3]
                comment = cell[4]
                mylist = cell[5]

                cm_cor = (view + mylist) / (view + comment + mylist)
                shapedOutputs[-1].append(
                    [view + comment * cm_cor + mylist ** 2 / view * 2]
                )

    x_train = []
    y_train = []
    for i in range(19):
        x_train += shapedInputs[i]
        y_train += shapedOutputs[i]
    x_test = shapedInputs[19]
    y_test = shapedOutputs[19]

    x_train = np.array(x_train, dtype = np.float32)
    x_test  = np.array(x_test,  dtype = np.float32)
    y_train = 100 * np.log10(np.array(y_train, dtype = np.float32))
    y_test  = 100 * np.log10(np.array(y_test,  dtype = np.float32))

    N = len(x_train)
    N_test = len(x_test)
    perm = np.arange(len(x_train) + len(x_test))
    # perm = np.random.permutation(N + N_test)

    # train_loss = [[] for i in range(5)]
    # train_acc  = [[] for i in range(5)]
    test_loss = [[] for i in range(N_model)]
    test_acc  = [[] for i in range(N_model)]
    test_data = np.zeros((N_test, N_model), np.float)

    if args.gpu:
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

        for i in range(0, N_test, batchsize):
            x_batch = x_test[i:i+batchsize]
            y_batch = y_test[i:i+batchsize]

            for j in range(N_model):
                # 順伝播させて誤差と精度を算出
                loss, op = model[j].error(x_batch, y_batch.reshape((len(y_batch),1)), train = False)
                sum_loss[j] += loss.data
                if epoch == n_epoch - 1:
                    size = batchsize if i + batchsize < N_test else N_test - i
                    op = cuda.to_cpu(op)
                    test_data[i:i+size, j] = op.reshape(size)

        for j in range(N_model):
            # テストデータでの誤差と、正解精度を表示
            print('test{0} mean loss={1}'.format(j, sum_loss[j] / N_test))
            test_loss[j].append(sum_loss[j] / N_test)

    elapsedTime = time.time() - startTime
    print('Total Time: {0}[m]'.format(elapsedTime / 60))

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

        if args.gpu:
            y_test = cuda.to_cpu(y_test)

        index = np.argsort(y_test, axis = 0)
        plt_data = np.append(y_test[index[:,0],:], test_data[index[:,0],:], axis = 1)
        # dump = list(zip(*test_data))
        # dump.sort()
        # plt_data = list(zip(*dump))

        plt.plot(plt_data[:,0], range(N_test), label = 'Ans.')
        for i in range(N_model):
            plt.plot(plt_data[:,i+1],range(N_test), label = config[i])
        plt.legend()
        plt.show()

def model_test():
    model = [None for i in range(N_model)]

    lfile = core.InitChartfile()
    x_dump = xp.array(lfile.x[-N_test:], dtype = xp.float32)
    y_dump = 100 * xp.log10(xp.array(lfile.vocaran[-N_test:], dtype = xp.float32))

    N = len(x_dump) - N_test
    perm = xp.arange(len(x_dump))

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
        y = model24(xp.array(x, dtype = np.float32).reshape((1, len(x))))
        return y
    else:
        return None

def main():
    learn()

argparser = argparse.ArgumentParser(
description = "U.Orihara Analyzer: analyze core module for utako with chainer."
)
argparser.add_argument('-v', '--verbose',
help = "Select verbose level. "\
+ "1:CRITICAL | 2:ERROR | 3:WARNING(default) | 4:INFO | 5:DEBUG",
action = 'count',
default = 3,
# type = int,
# choices = range(1,6)
)
argparser.add_argument('-e', '--epoch',
help = "Sets iteration epoch. Default is 50",
type = int,
nargs = '?',
default = 50
)
argparser.add_argument('-b', '--batch',
help = "Sets batch size. Default is 1000",
type = int,
nargs = '?',
default = 1000
)
argparser.add_argument('-g', '--gpu',
help = "Use first GPU if flag exists. Default is False",
action = 'store_true'
)

args = argparser.parse_args()

print(args)

if args.gpu:
    cuda.get_device(0).use()  # Make a specified GPU current

config = [[200,20],
          [200,20],
          [200,20]]
batchsize = args.batch
n_epoch = args.epoch

N_model = len(config)

if __name__ == '__main__':
    main()
