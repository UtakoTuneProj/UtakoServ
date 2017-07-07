import matplotlib.pyplot as plt
import numpy as np
from chainer import cuda, Variable, FunctionSet, optimizers
import chainer.functions  as F
import sys
import random

f = lambda x,y: x*y

if __name__ == '__main__':

    batchsize = 10
    n_epoch = 5
    n_units = 100

    N = 81
    N_test = 20

    thresh = 30

    model = FunctionSet(
        l1 = F.Linear(2, n_units),
        l2 = F.Linear(n_units, n_units),
        l3 = F.Linear(n_units, 2)
    )

    def forward(x_data, y_data, train = True):
        x,t = Variable(x_data), Variable(y_data)
        h1 = F.relu(model.l1(x))
        h2 = F.relu(model.l2(h1))
        y = model.l3(h2)

        print(x_data, y.data, t.data)

        return F.softmax_cross_entropy(y,t), F.accuracy(y,t)

    optimizer = optimizers.Adam()
    optimizer.setup(model.collect_parameters())

    train_loss = []
    train_acc  = []
    test_loss = []
    test_acc  = []

    l1_W = []
    l2_W = []

    dump = [ [[i,j], 1 if f(i,j) > thresh else 0]
            for i in range(1,10) for j in range(1,10)]
    [x_dump, y_dump] = zip(*dump)
    x_train = np.array(x_dump, dtype = np.float32)
    y_train = np.array(y_dump, dtype = np.int32)

    gena = [random.random() * 9 + 1 for i in range(20)]
    genb = [random.random() * 9 + 1 for i in range(20)]
    dump = [ [[i,j], 1 if f(i,j) > thresh else 0]
            for i in gena for j in genb]
    [x_dump, y_dump] = zip(*dump)
    x_test = np.array(x_dump, dtype = np.float32)
    y_test = np.array(y_dump, dtype = np.int32)

    # Learning loop
    for epoch in range(1, n_epoch+1):
        print('epoch', epoch)

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
            loss, acc = forward(x_batch, y_batch)
            # 誤差逆伝播で勾配を計算
            loss.backward()
            optimizer.update()
            sum_loss     += float(cuda.to_cpu(loss.data)) * batchsize
            sum_accuracy += float(cuda.to_cpu(acc.data)) * batchsize

        # 訓練データの誤差と、正解精度を表示
        print('train mean loss={}, accuracy={}'.format(sum_loss / N, sum_accuracy / N))

        train_loss.append(sum_loss / N)
        train_acc.append(sum_accuracy / N)

        # evaluation
        # テストデータで誤差と、正解精度を算出し汎化性能を確認
        sum_accuracy = 0
        sum_loss     = 0
        for i in range(0, N_test, batchsize):
            x_batch = x_test[i:i+batchsize]
            y_batch = y_test[i:i+batchsize]

            # 順伝播させて誤差と精度を算出
            loss, acc = forward(x_batch, y_batch, train=False)

            sum_loss     += float(cuda.to_cpu(loss.data)) * batchsize
            sum_accuracy += float(cuda.to_cpu(acc.data)) * batchsize

        # テストデータでの誤差と、正解精度を表示
        print('test  mean loss={}, accuracy={}'.format(sum_loss / N_test, sum_accuracy / N_test))
        test_loss.append(sum_loss / N_test)
        test_acc.append(sum_accuracy / N_test)

        # 学習したパラメーターを保存
        l1_W.append(model.l1.W)
        l2_W.append(model.l2.W)

    # 精度と誤差をグラフ描画
    plt.plot(range(len(train_acc)), train_acc)
    plt.plot(range(len(test_acc)), test_acc)
    plt.legend(["train_acc","test_acc"])
    plt.show()
