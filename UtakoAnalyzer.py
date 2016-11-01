# coding: utf-8
import sys
import numpy as np
from chainer import cuda, Variable, optimizers, Chain
import chainer.functions  as F
import chainer.links as L
try:
    import matplotlib.pyplot as plt
except:
    pass

import UtakoServCore as core
from ChartVisualizer import ChartData

class Chartfile(core.JSONfile):
    def __init__(self, path, encoding = 'utf-8'):
        super().__init__(path, encoding = encoding)
        dump = self.read()
        self.x = []
        self.y = []
        for mov in dump:
            self.x.append([])
            for cell in mov[0:-1]:
                self.x[-1].extend(cell)
            ydump = ChartData(mov[-1])
            self.y.append(ydump.vocaran)


class UtakoModel(Chain):
    def __init__(self, n_units = 50):
        super(UtakoModel, self).__init__(
            l1 = L.Linear(96, n_units),
            l2 = L.Linear(n_units, n_units),
            l3 = L.Linear(n_units, 1)
        )

    def __call__(self, x):
        h1 = F.relu(self.l1(x))
        h2 = F.relu(self.l2(h1))
        y = self.l3(h2)
        return y

    def error(self, x_data, y_data, train = True):
        y = self(Variable(x_data))
        t = Variable(y_data)
        if not train:
            ret = [t.data[0][0], y.data[0][0]]
        else:
            ret = None

        return F.mean_squared_error(y,t), ret

def learn():

    batchsize = 100
    n_epoch = 5000
    N_test = 200

    model = UtakoModel(n_units = 50)
    optimizer = optimizers.Adam()
    optimizer.setup(model)

    train_loss = []
    train_acc  = []
    test_loss = []
    test_acc  = []

    test_data = []

    l1_W = []
    l2_W = []

    lfile = Chartfile('dat/chartlist_init.json')
    x_dump = np.array(lfile.x, dtype = np.float32)
    y_dump = 100 * np.log10(np.array(lfile.y, dtype = np.float32))

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
        sum_accuracy = 0
        sum_loss = 0
        # 0〜Nまでのデータをバッチサイズごとに使って学習
        for i in range(0, N, batchsize):
            x_batch = x_train[perm[i:i+batchsize]]
            y_batch = y_train[perm[i:i+batchsize]]

            # 勾配を初期化
            optimizer.zero_grads()
            # 順伝播させて誤差と精度を算出
            loss, dump = model.error(x_batch, y_batch.reshape((len(y_batch),1)))
            # 誤差逆伝播で勾配を計算
            loss.backward()
            optimizer.update()
            sum_loss += loss.data * batchsize

        # 訓練データの誤差と、正解精度を表示
        print('train mean loss={}'.format(sum_loss / N))
        train_loss.append(sum_loss / N)

        # evaluation
        # テストデータで誤差と、正解精度を算出し汎化性能を確認
        sum_loss     = 0
        test_data.append([])
        for i in range(0, N_test):
            x_batch = x_test[i:i+1]
            y_batch = y_test[i:i+1]

            # 順伝播させて誤差と精度を算出
            loss,dump = model.error(x_batch, y_batch.reshape((len(y_batch),1)), train = False)
            test_data[-1].append(dump)

            sum_loss += loss.data

        # テストデータでの誤差と、正解精度を表示
        print('test  mean loss={}'.format(sum_loss / N_test))
        test_loss.append(sum_loss / N_test)

    # 精度と誤差をグラフ描画
    plt.plot(range(len(train_loss)), train_loss)
    plt.plot(range(len(test_loss)), test_loss)
    plt.legend(["train","test"])
    plt.yscale('log')
    plt.show()

    test_data[0].sort()
    test_data[int(n_epoch / 2)].sort()
    test_data[-1].sort()
    plt_data_init = [list(x) for x in zip(*test_data[0])]
    plt_data_cent = [list(x) for x in zip(*test_data[int(n_epoch / 2)])]
    plt_data_last = [list(x) for x in zip(*test_data[-1])]

    plt.plot(plt_data_init[0],range(N_test))
    plt.plot(plt_data_last[1],range(N_test))
    plt.legend(['Ans.', 'last'])
    plt.show()

def analyze():
    pass

def main():
    learn()

if __name__ == '__main__':
    main()
