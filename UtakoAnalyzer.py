# coding: utf-8
import sys
import numpy as np
from chainer import cuda, Variable, FunctionSet, optimizers
import chainer.functions  as F
try:
    import matplotlib.pyplot as plt
except:
    pass

import UtakoServCore as core
from ChartVisualizer import ChartData

class Chartfile(core.JSONfile):
    def __init__(self,path, encoding = 'utf-8'):
        core.JSONfile.__init__(self, path, encoding = encoding)
        dump = self.read()
        self.x = []
        self.y = []
        for mov in dump:
            self.x.append([])
            for cell in mov[0:-1]:
                self.x[-1].extend(cell)
            ydump = ChartData(mov[-1])
            self.y.append(ydump.vocaran)

def learn():
    batchsize = 1
    n_epoch = 300
    n_units = 20

    model = FunctionSet(l1 = F.Linear(96, n_units),
        l2 = F.Linear(n_units, n_units),
        l3 = F.Linear(n_units, 1)
    )

    def forward(x_data, y_data, train = True):
        x,t = Variable(x_data), Variable(y_data)
        h1 = F.relu(model.l1(x))
        h2 = F.relu(model.l2(h1))
        y = model.l3(h2)
        if not train:
            print(np.hstack((y.data,t.data)))

        return F.mean_squared_error(y,t)

    optimizer = optimizers.Adam()
    optimizer.setup(model.collect_parameters())

    train_loss = []
    train_acc  = []
    test_loss = []
    test_acc  = []

    l1_W = []
    l2_W = []

    lfile = Chartfile('dat/chartlist_init.json')
    x_dump = np.array(lfile.x, dtype = np.float32)
    y_dump = 100 * np.log10(np.array(lfile.y, dtype = np.float32))

    N_test = 100
    N = len(x_dump) - N_test
    perm = np.arange(len(x_dump))
    # perm = np.random.permutation(N + N_test)

    x_train = x_dump[perm[:-N_test]]
    y_train = y_dump[perm[:-N_test]]
    x_test = x_dump[perm[-N_test:]]
    y_test = y_dump[perm[-N_test:]]
    
    

    # Learning loop
    for epoch in range(n_epoch):
        print('epoch', epoch + 1)

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
            loss = forward(x_batch, y_batch.reshape((len(y_batch),1)))
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
        for i in range(0, N_test, batchsize):
            x_batch = x_test[i:i+batchsize]
            y_batch = y_test[i:i+batchsize]

            # 順伝播させて誤差と精度を算出
            loss = forward(x_batch, y_batch.reshape((len(y_batch),1)), train = False)

            sum_loss += loss.data * batchsize

        # テストデータでの誤差と、正解精度を表示
        print('test  mean loss={}'.format(sum_loss / N_test))
        test_loss.append(sum_loss / N_test)

        # 学習したパラメーターを保存
        l1_W.append(model.l1.W)
        l2_W.append(model.l2.W)

    # 精度と誤差をグラフ描画
    plt.plot(range(len(train_loss)), train_loss)
    plt.plot(range(len(test_loss)), test_loss)
    plt.legend(["train","test"])
    plt.yscale('log')
    plt.show()

def analyze():
    pass

def main():
    learn()

if __name__ == '__main__':
    main()
