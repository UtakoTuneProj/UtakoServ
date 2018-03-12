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

class SongAutoEncoderChain(ChainList):
    def __init__(self, structure):
        # structure:
        # list of Chain
        # example is shown in conf/sae.yaml
        self.links = []
        self.funcs = []

        for layer in structure:
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

            self.links.append(cls(
                **args,
                **layer['link']['args']
            ))

            funcs_sub = []
            func_defs = layer['func']
            if type(func_defs) not in ( list, tuple ):
                func_defs = ( func_defs, )
            for func_def in func_defs:
                functype = func_def['type']
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
                elif functype == 'pass':
                    func = F.broadcast
                elif functype == 'drop':
                    func = F.dropout
                elif functype == 'norm':
                    func = F.normalize
                else:
                    raise TypeError('func type {} cannot be recognized'.format(functype))
                funcs_sub.append(functools.partial(func, **func_def['args']))

            self.funcs.append(funcs_sub)
            
        super().__init__(*self.links)

    def __call__(self, x):
        h = x
        for link, funcs in zip(self.links, self.funcs):
            h = link(h)
            for func in funcs:
                h = func(h)
        return h

    def reset_state(self):
        for layer in self.links:
            if type(layer) == L.LSTM:
                layer.reset_state()

    def error(self, x_data, y_data, train = True):
        y = self(Variable(x_data))
        t = Variable(y_data)

        return F.mean_squared_error(y,t), y.data

class SongAutoEncoder:
    def __init__(
        self,
        structure,
        name = 'song_AE',
        n_epoch = 300,
        batchsize = 50,
        x_train = None,
        x_test = None,
        isgpu = True,
        isgui = True,
        preprocess = lambda x: x,
        postprocess = lambda x: x,
        modelclass = SongAutoEncoderChain
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
        self.set_model(structure, modelclass, self.basename+'.model')
        self.set_data(x_train, x_test)

    def set_model(self, structure, modelclass, modelfile = None):
        self.structure = structure
        self.in_size = structure[0]
        self.model = modelclass(structure = self.structure)

        if (modelfile is not None) and (os.path.isfile(modelfile)):
            serializers.load_npz(modelfile, self.model)

        if self.isgpu:
            self.model.to_gpu()  # Copy the model to the GPU

        self.optimizer = optimizers.Adam()
        self.optimizer.setup(self.model)

    def set_data(self, train, test):
        if type(train) != np.ndarray or type(test) != np.ndarray :
            if os.path.isfile('train.npy') and os.path.isfile('test.npy'):
                self.x_train = np.load('train.npy')
                self.x_test = np.load('test.npy')
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
        random = False,
        batchsize = None,
    ):
        data_size, length = data.shape
        if batchsize is None:
            batchsize = self.batchsize

        if data_size % batchsize != 0:
            data = np.append(
                data,
                data[np.random.permutation(
                    batchsize - data_size % batchsize
            ) % data_size], axis = 0)

        data_size, length = data.shape
        if random:
            np.random.shuffle(data)
        batch = data.reshape(
            data_size // batchsize,
            batchsize,
            1,
            1,
            length
        ).transpose(0,2,1,3,4)
            
        batch = self.preprocess(batch)

        if self.isgpu:
            batch = cuda.to_gpu(batch)

        return batch 
    
    def unify_batch(self, batch):
        batch_count, time_count, batchsize, channels, timesize = batch.shape
        if self.isgpu:
            batch = cuda.to_cpu(batch)
        batch = self.postprocess(batch)
        res = batch.reshape(batch_count * batchsize, time_count * channels * timesize)
        return res

    def challenge(self, batch, isTrain = False, noise_scale = 0.10):
        train_status = chainer.config.train
        chainer.config.train = isTrain
        
        batch_count, time_count, batchsize, channels, timesize = batch.shape
        prediction   = cupy.zeros(batch.shape)
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
                if False:
                    noise = np.random.normal(scale = noise_scale, size = (batchsize, channels, timesize))
                else:
                    noise = np.zeros((batchsize, channels, timesize))
                noise = np.array(noise, dtype = np.float32)
                if self.isgpu:
                    noise = cuda.to_gpu(noise)
                    
                # 順伝播させて誤差と精度を算出
                moment_error, moment_prediction = self.model.error(batch[i,j,:,:,:] + noise, batch[i,j,:,:,:])
                if isTrain:
                    # 誤差逆伝播で勾配を計算
                    moment_error.backward()
                    self.optimizer.update()
                loss += moment_error.data
                prediction[i, j, :, :, :] = moment_prediction
            sum_loss += loss

        chainer.config.train = train_status
        return float(sum_loss / batch_count / batchsize), prediction

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

    def visualize_wave(self, waves, title = None, **kwargs):
        if type(waves) is dict:
            for key in waves:
                s = waves[key]
                librosa.display.waveplot(s, label = key, alpha = 0.4, **kwargs)
        elif type(waves) in (list, np.ndarray):
            for i, s in enumerate(args):
                librosa.display.waveplot(s, label = str(i), alpha = 0.4, **kwargs)
        else:
            raise TypeError('SAE.visualize_wave only accepts dict, list or np.ndarray as waves. Not {}'.format(type(waves)))

        plt.title(title)
        plt.legend()
        plt.show()

    def write_wave(self, wave, fname = None):
        if fname is None:
            fname = self.basename + '.wav'
        librosa.output.write_wav(fname, wave, sr=5513)

    def __call__(self, mode, mvid = None, modelfile = None):
        pass

    def learn(self):
        startTime = time.time()

        train_batch = self.get_batch(self.x_train, random = True)
        test_batch  = self.get_batch(self.x_test)
        train_loss  = []
        test_loss   = []

        try:
            # Learning loop
            for epoch in range(self.n_epoch):
                print('epoch', epoch + 1, flush = True)

                with chainer.using_config('train', True):
                    res, _ = self.challenge(train_batch, isTrain = True, noise_scale = 0.07 * np.log(epoch+10) - 0.07)
                    # # 訓練データの誤差と、正解精度を表示
                    print('train mean loss={}'.format(res))
                    train_loss.append(res)

                # evaluation
                # テストデータで誤差と、正解精度を算出し汎化性能を確認

                with chainer.using_config('train', False):
                    res, _ = self.challenge(test_batch, isTrain = False)
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

    def examine(self, trial = None, write_wav = True):
        # trial: list/dict: list/dict for plot waveform and/or save wave if trial is None:
        if trial is None:
            trial = {
                'train': self.x_train[334],
                'test' : self.x_test[893],
            }

        if type(trial) == dict:
            trial_keys, trial_values = zip(*trial.items())
            x_trial = np.array(trial_values)
        elif type(trial) in (list, np.ndarray):
            trial_keys = range(len(trial))
            x_trial = trial
        else:
            raise TypeError('SAE.examine only accepts dict, list or np.ndarray as trial. Not {}'.format(type(trial)))

        train_batch = self.get_batch(self.x_train)
        test_batch  = self.get_batch(self.x_test)
        trial_batch = self.get_batch(x_trial)

        with chainer.using_config('train', False):
            train_loss, _ = self.challenge(train_batch, isTrain = False)
            test_loss, _ = self.challenge(test_batch, isTrain = False)
            _, trial_predict_batch = self.challenge(trial_batch, isTrain = False)
            print('train mean loss={}'.format(train_loss))
            print('test mean loss={}'.format(test_loss))

        trial_predict = self.unify_batch(trial_predict_batch)

        for i, key in enumerate(trial_keys):
            waves = dict(
                teacher = x_trial[i],
                predict = trial_predict[i],
            )
            if self.isgui:
                self.visualize_wave(
                    waves = waves,
                    title = key,
                )

            if write_wav:
                for keyw in waves:
                    self.write_wave(
                        waves[keyw],
                        fname = '{}_{}_{}.wav'.format(self.basename, key, keyw),
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
