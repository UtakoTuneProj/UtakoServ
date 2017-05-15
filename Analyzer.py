# coding: utf-8
# Analyzer: UtakoChainer core module
import sys
import time
import argparse

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
help = "Sets iteration epoch. Default is 250",
type = int,
nargs = '?',
default = 250
)
argparser.add_argument('-b', '--batch',
help = "Sets batch size. Default is 1000",
type = int,
nargs = '?',
default = 1000
)
argparser.add_argument('-t', '--testgroup',
help = "Select which analyze group to test data. Default is 19 (the last).",
type = int,
nargs = '?',
choices = range(20),
default = 19
)
argparser.add_argument('-m', '--mode',
help  = "Select analyzer mode. " +\
        "l/learn : Learn from database. (Default) | " +\
        "x/examine : Examine learned model. | " +\
        "a/analyze : Analyze specified movie. -i param is needed. | " ,
type = str,
nargs = '?',
choices = ['l', 'x', 'a', 'learn', 'examine', 'analyze'],
default = 'l',
)
argparser.add_argument('-f', '--modelfile',
help = "Specify which model to examine or analyze. Use with -m x or -m a.",
type = str,
nargs = '+',
default = ['Network/chart24h.model',],
)
argparser.add_argument('-i', '--mvid',
help = "Specify which movie to analyze. Use with -m a.",
type = str,
nargs = '?',
)
argparser.add_argument('-g', '--gpu',
help = "Use first GPU if flag exists. Default is False. Only usable on learn mode",
action = 'store_true'
)

args = argparser.parse_args()

if __name__ == '__main__':
    print("importing modules...")

import numpy as np
from chainer import cuda, Variable, optimizers, Chain, ChainList, serializers
import chainer.functions  as F
import chainer.links as L
try:
    import matplotlib.pyplot as plt
    GUI = True
except:
    GUI = False

import sql
cmdf = sql.cmdf

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

def fetch(isTrain = False, mvid = None):
    if mvid == None and not isTrain:
        raise ValueError('Neither mvid nor isTrain was given.')

    db = sql.DataBase('test')
    qtbl = sql.QueueTable(db)
    ctbl = sql.ChartTable(db)

    shapedInputs = []
    shapedOutputs = []

    if isTrain:
        rawCharts = []

        print("Fetching from database...")
        for i in range(20):
            rawCharts.append(db.get(
                'select chart.* from chart join status using(ID) ' +
                'where status.analyzeGroup = ' + str(i) + ' and isComplete = 1 ' +
                'order by ID, epoch'
            ))
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

    else:
        rawCharts = db.get(
            "select chart.* from chart join status using(ID) " +
            "where ID = '" + mvid + "' order by chart.epoch"
        )

        if len(rawCharts) < 24:
            raise ValueError(mvid + ' is not analyzable')

        for i,cell in enumerate(rawCharts):
            if i != 24:
                shapedInputs.extend(cell[2:])

    return [shapedInputs, shapedOutputs]

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

    fetchData = fetch(isTrain = True)

    x_train = []
    y_train = []
    for i in range(20):
        if i == args.testgroup:
            x_test = fetchData[0][i]
            y_test = fetchData[1][i]
        else:
            x_train += fetchData[0][i]
            y_train += fetchData[1][i]

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
            size = len(y_batch)

            for j in range(N_model):
                # 順伝播させて誤差と精度を算出
                loss, op = model[j].error(
                    x_batch, y_batch.reshape((size,1)), train = False
                )
                sum_loss[j] += loss.data * size
                if epoch == n_epoch - 1:
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

def examine(modelpath, n_units = 200, layer = 20):
    f = fetch(isTrain = True)
    x = np.array(f[0][args.testgroup], dtype = np.float32)
    y = 100 * np.log10(np.array(f[1][args.testgroup], dtype = np.float32))

    N_test = len(y)

    model = ChartModel(n_units = n_units, layer = layer)
    serializers.load_npz(modelpath, model)
    e, l = model.error(x, y.reshape((len(y), 1)), train = False)

    if GUI:
        index = np.argsort(y, axis = 0)
        y = y[index[:,0],:]
        l = l[index[:,0],:]
        plt.plot(y, range(N_test), label = 'Ans.')
        plt.plot(l, range(N_test), label = 'Exam.')
        plt.legend()
        plt.show()

        plt.hist(l-y, bins = 50)
        plt.show()

    return e.data, np.mean(l-y), np.std(l-y)

def analyze(mvid, n_units = 200, layer = 20):
    model = ChartModel(n_units = n_units, layer = layer)
    serializers.load_npz(args.modelfile[0], model)

    [x, _] = fetch(mvid = mvid)
    return model(np.array(x, dtype = np.float32).reshape((1, len(x)))).data[0][0]

def main():
    if args.mode in ['l', 'learn']:
        learn()
    elif args.mode in ['x', 'examine']:
        for mp in args.modelfile:
            print(examine(modelpath = mp))
    else:
        print(analyze(args.mvid))

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
