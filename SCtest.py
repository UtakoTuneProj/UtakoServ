#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __init__ import utako, yaml, np, gc, wav, songs_label

def sc_test(
    fname,
    wav = wav,
    label = songs_label,
    n_train = 100000,
    n_test = 10000,
    randomize = True,
    **kwargs
):
    with open(fname) as f:
        structure = yaml.load(f)
    
    if randomize:
        index = np.random.permutation(wav.shape[0])
    else:
        index = np.arange(wav.shape[0])
    train_index = index[:n_train]
    test_index = index[n_train:n_train + n_test]
    SC = \
        utako.analyzer.song_classifier.SongClassifier(
            structure = structure,
            x_train = wav[train_index, :],
            y_train = label[train_index],
            x_test  = wav[test_index, :],
            y_test  = label[test_index],
            **kwargs
        )
    SC.learn()
    gc.collect()

    return SC, train_index, test_index

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Utako Tune Song Classifier Trainer"
    )

    parser.add_argument(
        "modelfile_name",
        help="*.yaml model file to define classifier architecture"
    )
    parser.add_argument(
        "--use-gpu", "-g",
        action="store_true",
        help="use GPU acceleration in training if specified"
    )
    parser.add_argument(
        "--skip-randomize", "-R",
        action="store_true",
        help="Do not randomize training data (not recommended)"
    )
    parser.add_argument(
        "--epoch", "-e",
        type=int, default=100,
        help="number of training epochs"
    )
    parser.add_argument(
        "--batchsize", "-b",
        type=int, default=100,
        help="size of training batch"
    )
    parser.add_argument(
        "--train-samples", "-t",
        type=int, default=800,
        help="samples count of training data"
    )
    parser.add_argument(
        "--test-samples", "-s",
        type=int, default=200,
        help="samples count of evaluation data"
    )

    args = parser.parse_args()

    sc_test(
        fname       = args.modelfile_name,
        isgpu       = args.use_gpu,
        randomize   = not args.skip_randomize,
        n_epoch     = args.epoch,
        n_train     = args.train_samples,
        n_test      = args.test_samples,
        batchsize   = args.batchsize,
    )

