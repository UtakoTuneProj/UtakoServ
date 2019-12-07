#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Analyzer: UtakoChainer core module
from utako.common_import import *
import gc
import chainer
import functools
import librosa
import librosa.display
import matplotlib.pyplot as plt
import scipy.fftpack as fft
import datetime
from pathlib import Path

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
                args[ 'initialW' ] = X['updater/model:main/predictor/{}/W'.format(layer['link']['init']['number'])]
                args[ 'initial_bias' ] = X['updater/model:main/predictor/{}/b'.format(layer['link']['init']['number'])]

            links.append(cls(
                **args,
                **layer['link']['args']
            ))
            if layer.get('freeze'):
                links[-1].disable_update()

            funcs_sub = []
            func_defs = layer['func']
            if type(func_defs) not in ( list, tuple ):
                func_defs = ( func_defs, )
            for func_def in func_defs:
                functype = func_def['type']
                args = func_def['args']
                if functype == 'pool':
                    func = F.max_pooling_nd
                elif functype == 'avgpool':
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
                elif functype == 'abs':
                    func = F.absolute
                elif functype == 'reshape':
                    func = F.reshape
                    args['shape'] = [-1,] + args['shape']
                elif functype == 'transpose':
                    func = F.transpose
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
        y = self(x_data)
        t = Variable(y_data.argmax(axis=-1).reshape(-1))

        return F.softmax_cross_entropy(y,t)
#       return F.huber_loss(x = y, t = t, delta = 0.5), y.data

class SongClassifier:
    def __init__(
        self,
        structure,
        name = 'song_classifier',
        n_epoch = 300,
        save_epoch = 20,
        batchsize = 50,
        x_train = None,
        y_train = None,
        x_test = None,
        y_test = None,
        isgpu = True,
        isgui = True,
        preprocess = lambda x: x,
        postprocess = lambda x: x,
        modelclass = SongClassifierChain,
        **kwargs
    ):
        self.n_epoch    = n_epoch
        self.save_epoch = save_epoch
        self.name       = name
        self.batchsize  = batchsize
        self.isgpu      = isgpu 
        self.isgui      = isgui 
        self.preprocess = preprocess
        self.postprocess= postprocess
        self.result_path  = Path(
            'result/{name}/{time:%Y}/{time:%m%d}/{time:%H%S}'.format(
                name=name,
                time=datetime.datetime.now()
        ))
        self.result_path.mkdir(parents=True)
        self.structure = structure
        self.modelclass = modelclass
        self.model_kwargs = kwargs

        self.device = 0 if self.isgpu else -1  # Make a specified GPU current

        self.set_model(modelclass, **kwargs)
        self.set_data(x_train, y_train, x_test, y_test)
        self.set_trainer()

    def set_model(self, modelclass, **kwargs):
        self.predictor = modelclass(structure = self.structure, **kwargs)
        self.model = L.Classifier(self.predictor)

        if self.isgpu:
            self.model.to_gpu(self.device)  # Copy the model to the GPU

        self.optimizer = optimizers.Adam()
        self.optimizer.setup(self.model)

    def set_data(self, x_train, y_train, x_test, y_test):
        if type(x_train) != np.ndarray \
        or type(y_train) != np.ndarray \
        or type(x_test) != np.ndarray \
        or type(y_test) != np.ndarray :
            raise TypeError('x, y data must be np.ndarray')

        else:
            self.train = chainer.datasets.TupleDataset(x_train, y_train)
            self.test = chainer.datasets.TupleDataset(x_test, y_test)
    
    def set_trainer(self):
        self.train_iter = chainer.iterators.SerialIterator(self.train, self.batchsize)
        self.test_iter = chainer.iterators.SerialIterator(self.test, self.batchsize, repeat=False, shuffle=False)

        updater = chainer.training.updaters.StandardUpdater(self.train_iter, self.optimizer, device=self.device)
        trainer = chainer.training.Trainer(updater, (self.n_epoch, 'epoch'), out=str( self.result_path ))

        self.extend_trainer(trainer)
        self.trainer = trainer

    def extend_trainer(self, trainer):
        extensions = chainer.training.extensions
        trainer.extend(extensions.Evaluator(self.test_iter, self.model, device=self.device))
        trainer.extend(extensions.snapshot(
                filename='snapshot_epoch_{.updater.epoch}.model'
            ), trigger=(
                self.save_epoch,
                'epoch'
            )
        )
        trainer.extend(extensions.snapshot(
                filename='final.model'
            ), trigger=(
                self.n_epoch,
                'epoch'
            )
        )
        trainer.extend(extensions.LogReport())
        trainer.extend(extensions.PrintReport([
            'epoch', 'main/loss', 'validation/main/loss',
            'main/accuracy', 'validation/main/accuracy', 'elapsed_time',
        ]))
        trainer.extend(extensions.ProgressBar())

        if extensions.PlotReport.available():
            trainer.extend(extensions.PlotReport(
                y_keys=['main/loss', 'validation/main/loss'],
                x_key='epoch',
                file_name='loss.png'
            ))
            trainer.extend(extensions.PlotReport(
                y_keys=['main/accuracy', 'validation/main/accuracy'],
                x_key='epoch',
                file_name='accuracy.png'
            ))

    def learn(self):
        self.trainer.run()

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
