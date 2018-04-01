#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Analyzer: UtakoChainer core module
from utako.common_import import *
import chainer
import functools
import librosa
import librosa.display
from utako.presenter.wave_loader import WaveLoader
import matplotlib.pyplot as plt
import scipy.fftpack as fft

class SongClassifierChain(ChainList):
    def __init__(self, structure):
        # structure:
        # list of Chain
        # example is shown in conf/sae.yaml
        self.encode_links = []
        self.encode_funcs = []
        self.decode_links = []
        self.decode_funcs = []
         
        links = self.encode_links
        funcs = self.encode_funcs

        for i, layer in enumerate(structure):
            linktype = layer['link']['type']
            if linktype == 'conv':
                cls = L.ConvolutionND
            elif linktype == 'deconv':
                cls = L.DeconvolutionND
            elif linktype == 'linear':
                cls = L.Linear
            elif linktype == 'lstm':
                cls = L.LSTM
            elif linktype == 'pass':
                cls = L.Parameter
            else:
                raise TypeError('link type {} cannot be recognized'.format(linktype))
            
            args = {}

            if 'init' in layer['link']:
                X = np.load(layer['link']['init']['fname'])
                args[ 'initialW' ] = X['{}/W'.format(layer['link']['init']['number'])]
                args[ 'initial_bias' ] = X['{}/b'.format(layer['link']['init']['number'])]

            links.append(cls(
                **args,
                **layer['link']['args']
            ))

            funcs_sub = []
            func_defs = layer['func']
            if type(func_defs) not in ( list, tuple ):
                func_defs = ( func_defs, )
            for func_def in func_defs:
                functype = func_def['type']
                args = func_def['args']
                if functype == 'pool':
                    func = F.average_pooling_nd
                elif functype == 'unpool':
                    func = F.unpooling_nd 
                elif functype == 'relu':
                    func = F.relu
                elif functype == 'lrelu':
                    func = F.leaky_relu
                elif functype == 'sigmoid':
                    func = F.sigmoid
                elif functype == 'tanh':
                    func = F.tanh
                elif functype == 'reshape':
                    func = F.reshape
                    args['shape'] = [-1,] + args['shape']
                elif functype == 'pass':
                    func = F.broadcast
                elif functype == 'drop':
                    func = F.dropout
                elif functype == 'norm':
                    func = F.normalize
                else:
                    raise TypeError('func type {} cannot be recognized'.format(functype))
                funcs_sub.append(functools.partial(func, **func_def['args']))

            funcs.append(funcs_sub)

            if 'end_encode' in layer:
                if layer['end_encode']:
                    links = self.decode_links
                    funcs = self.decode_funcs
            
        super().__init__(*self.encode_links, *self.decode_links)

    def __call__(self, x):
        return self.decode(self.encode(x))

    def _calculate_layer(self, link, funcs, x):
#       print(x.shape)
        h = link(x)
        for func in funcs:
#           print(h.shape)
            h = func(h)
        return h 

    def encode(self, x):
        h = x
        for link, funcs in zip(self.encode_links, self.encode_funcs):
            h = self._calculate_layer(link, funcs, h)
        return h

    def decode(self, x):
        h = x
        for link, funcs in zip(self.decode_links, self.decode_funcs):
            h = self._calculate_layer(link, funcs, h)
        return h

    def reset_state(self):
        for layer in self.encode_links, self.decode_links:
            if type(layer) == L.LSTM:
                layer.reset_state()

    def error(self, x_data, y_data, train = True):
        y = self(Variable(x_data))
        t = Variable(y_data)

        return F.softmax_cross_entropy(y,t), y.data
#       return F.huber_loss(x = y, t = t, delta = 0.5), y.data

class SongClassifier:
    def __init__(
        self,
        structure,
        name = 'song_classifier',
        n_epoch = 300,
        batchsize = 50,
        x_train = None,
        y_train = None,
        x_test = None,
        y_test = None,
        isgpu = True,
        isgui = True,
        preprocess = lambda x: x,
        postprocess = lambda x: x,
        modelclass = SongClassifierChain
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
        self.set_model(structure, modelclass)
        self.set_data(x_train, y_train, x_test, y_test)

    def set_model(self, structure, modelclass):
        self.structure = structure
        self.model = modelclass(structure = self.structure)

        if self.isgpu:
            self.model.to_gpu()  # Copy the model to the GPU

        self.optimizer = optimizers.Adam()
        self.optimizer.setup(self.model)

    def set_data(self, x_train, y_train, x_test, y_test):
        if type(x_train) != np.ndarray \
        or type(y_train) != np.ndarray \
        or type(x_test) != np.ndarray \
        or type(y_test) != np.ndarray :
            raise TypeError('x, y data must be np.ndarray')

        else:
            self.x_train = x_train
            self.x_test  = x_test
            self.y_train = y_train
            self.y_test  = y_test

        self.N_train = len(self.x_train)
        self.N_test  = len(self.x_test)

    def get_batch(
        self,
        in_data,
        out_data,
        random = False,
        batchsize = None,
    ):

        in_data_size, in_length = in_data.shape
        out_data_size, out_length = out_data.shape
        if batchsize is None:
            batchsize = self.batchsize
        
        if in_data_size != out_data_size:
            raise TypeError(
                'in_data_size {} must be equal to out_data_size {}'.format(
                    in_data_size,
                    out_data_size
            ))
        else:
            data_size = in_data_size

        if data_size % batchsize != 0:
            add_index = np.random.permutation(
                batchsize - data_size % batchsize
            ) % data_size
            in_data = np.append(
                in_data,
                in_data[add_index], axis = 0
            )
            out_data = np.append(
                out_data,
                out_data[add_index], axis = 0
            )

        data_size, _ = in_data.shape
        if random:
            order = np.random.permutation(data_size)
            in_data = in_data[order]
            out_data = out_data[order]

        in_batch = in_data.reshape(
            data_size // batchsize,
            batchsize,
            1,
            1,
            in_length
        ).transpose(0,2,1,3,4)
        out_batch = out_data.reshape(
            data_size // batchsize,
            batchsize,
            1,
            1,
            out_length
        ).transpose(0,2,1,3,4)
            
        #batch = self.preprocess(batch)

        if self.isgpu:
            in_batch = cuda.to_gpu(in_batch)
            out_batch = cuda.to_gpu(out_batch)

        return in_batch, out_batch
    
    def unify_batch(self, batch):
        batch_count, time_count, batchsize, channels, timesize = batch.shape
        if self.isgpu:
            batch = cuda.to_cpu(batch)
        batch = self.postprocess(batch)
        res = batch.reshape(batch_count * batchsize, time_count * channels * timesize)
        return res

    def challenge(self, in_batch, out_batch, isTrain = False, noise_scale = 0.10):
        train_status = chainer.config.train
        chainer.config.train = isTrain

        batch = in_batch
        batch_count, time_count, batchsize, channels, timesize = batch.shape
        prediction   = cupy.zeros(out_batch.shape)
        sum_loss     = 0
        perm = np.arange(batch_count)
        if isTrain:
            np.random.shuffle(perm)
        for i in perm:
            loss = 0
            # initialize State
            self.model.reset_state()
            for j in np.arange(time_count):
                # 勾配を初期化
                self.model.cleargrads()
                # ノイズを付加
                if isTrain:
                    noise = np.random.normal(scale = noise_scale, size = (batchsize, channels, timesize))
                else:
                    noise = np.zeros((batchsize, channels, timesize))
                noise = np.array(noise, dtype = np.float32)
                if self.isgpu:
                    noise = cuda.to_gpu(noise)
                    
                # 順伝播させて誤差と精度を算出
                moment_error, moment_prediction = self.model.error(batch[i,j,:,:,:] + noise, out_batch[i,j,:,:,:])
                if isTrain:
                    # 誤差逆伝播で勾配を計算
                    moment_error.backward()
                    self.optimizer.update()
                loss += moment_error.data
                prediction[i, j, :, :, :] = moment_prediction
            sum_loss += loss

        chainer.config.train = train_status
        return float(sum_loss / batch_count / time_count), prediction

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

    def __call__(self, mode, mvid = None, modelfile = None):
        pass

    def learn(self):
        startTime = time.time()

        x_train_batch, y_train_batch = self.get_batch(
            self.x_train,
            self.y_train,
            random = True
        )
        x_test_batch, y_test_batch = self.get_batch(
            self.x_test,
            self.y_test
        )
        train_loss  = []
        test_loss   = []

        try:
            # Learning loop
            for epoch in range(self.n_epoch):
                print('epoch', epoch + 1, flush = True)

                with chainer.using_config('train', True):
                    res, _ = self.challenge(x_train_batch, y_train_batch, isTrain = True, noise_scale = 0.07 * np.log(epoch+10) - 0.07)
                    # # 訓練データの誤差と、正解精度を表示
                    print('train mean loss={}'.format(res))
                    train_loss.append(res)

                # evaluation
                # テストデータで誤差と、正解精度を算出し汎化性能を確認

                with chainer.using_config('train', False):
                    res, _ = self.challenge(x_test_batch, y_test_batch, isTrain = False)
                    # # 訓練データの誤差と、正解精度を表示
                    print('test mean loss={}'.format(res))
                    test_loss.append(res)

                if epoch % 50 == 0:
                    serializers.save_npz('{0}_{1:04d}.model'.format(self.basename, epoch), self.model)

        except KeyboardInterrupt:
            print('Interrupted')

        finally:
            elapsedTime = time.time() - startTime
            print('Total Time: {0}[min.]'.format(elapsedTime / 60))

            serializers.save_npz('{0}_{1:04d}.model'.format(self.basename, epoch), self.model)

            if self.isgui: 
                # 精度と誤差をグラフ描画
                # plt.plot(range(len(train_loss)), train_loss)
                self.visualize_loss(
                    train = train_loss,
                    test  = test_loss,
                )

            self.examine()

            with open('{}.json'.format(self.basename), 'w') as f:
                json.dump([train_loss, test_loss], f)

        return train_loss, test_loss

    def examine(self):
        # trial: list/dict: list/dict for plot waveform and/or save wave if trial is None:

        x_train_batch, y_train_batch = self.get_batch(self.x_train, self.y_train)
        x_test_batch, y_test_batch  = self.get_batch(self.x_test, self.y_test)

        with chainer.using_config('train', False):
            train_loss, _ = self.challenge(x_train_batch, y_train_batch, isTrain = False)
            test_loss, _ = self.challenge(x_test_batch, y_test_batch, isTrain = False)
            print('train mean loss={}'.format(train_loss))
            print('test mean loss={}'.format(test_loss))

        return train_loss, test_loss

#    def analyze():
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
