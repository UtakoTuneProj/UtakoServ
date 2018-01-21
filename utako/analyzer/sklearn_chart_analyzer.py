#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Analyzer: UtakoChainer core module
from common_import import *

argparser = argparse.ArgumentParser(
description = "U.Orihara Analyzer: analyze core module for utako with Linear Regression."
)
argparser.add_argument('-v', '--verbose',
help = "Select verbose level. "\
+ "1:CRITICAL | 2:ERROR | 3:WARNING(default) | 4:INFO | 5:DEBUG",
action = 'count',
default = 3,
# type = int,
# choices = range(1,6)
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
default = ['linRegAnaly.json',],
)
argparser.add_argument('-i', '--mvid',
help = "Specify which movie to analyze. Use with -m a.",
type = str,
nargs = '?',
)

args = argparser.parse_args()

if __name__ == '__main__':
    print("importing modules...")

import numpy as np
import sklearn.linear_model
try:
    import matplotlib.pyplot as plt
    GUI = True
except ImportError:
    GUI = False

import sql
cmdf = sql.cmdf

if __name__ == '__main__':
    print('imported modules')

class LinearRegressionAnalyzer(sklearn.linear_model.LinearRegression):
    def error(self, x, y):
        l = np.array([self.predict(x)]).T
        return ((l - y) ** 2).mean(axis = None), l

def learn():
    startTime = time.time()

    fetchData = sql.fetch(isTrain = True)
    linRegAnaly = LinearRegressionAnalyzer()

    x_train = []
    y_train = []
    for i in range(20):
        if i == args.testgroup:
            x_test = fetchData[0][i]
            y_test = fetchData[1][i]
        else:
            x_train += fetchData[0][i]
            y_train += fetchData[1][i]

    tmp = np.array(x_train, dtype = np.float32)
    x_train = np.log10(tmp + np.ones(tmp.shape))
    tmp = np.array(x_test,  dtype = np.float32)
    x_test  = np.log10(tmp + np.ones(tmp.shape))
    y_train = 100 * np.log10(np.array(y_train, dtype = np.float32))
    y_test  = 100 * np.log10(np.array(y_test,  dtype = np.float32))

    N = len(x_train)
    N_test = len(x_test)

    # Learn
    linRegAnaly.fit(x_train, y_train)

    elapsedTime = time.time() - startTime
    print('Total Time: {0}[m]'.format(elapsedTime / 60))

    with open('linRegAnaly.json', 'w') as f:
        stream = json.dump({
            'coef': list(map(float, linRegAnaly.coef_.flatten())),
            'intercept': float(linRegAnaly.intercept_[0])
        }, f)

    if GUI:
        index = np.argsort(y_test, axis = 0)
        plt_data = np.append(
            y_test[index[:,0],:],
            linRegAnaly.predict(x_test)[index[:,0],:],
            axis = 1
        )

        plt.plot(plt_data[:,0], range(N_test), label = 'Ans.')
        plt.plot(plt_data[:,1], range(N_test), label = 'Regr.')
        plt.legend()
        plt.show()

def examine(modelpath):
    f = sql.fetch(isTrain = True)
    tmp = np.array(f[0][args.testgroup], dtype = np.float32)
    x = np.log10(tmp + np.ones(tmp.shape))
    y = 100 * np.log10(np.array(f[1][args.testgroup], dtype = np.float32))

    N_test = len(y)

    with open(modelpath) as f:
        tmp = json.load(f)

    linRegAnaly = LinearRegressionAnalyzer()

    linRegAnaly.coef_ = np.array(tmp['coef'])
    linRegAnaly.intercept_ = np.array(tmp['intercept'])

    e, l = linRegAnaly.error(x, y)

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

    return e, np.mean(l-y), np.std(l-y)

def analyze(mvid):
    with open(args.modelfile[0]) as f:
        tmp = json.load(f)

    linRegAnaly = LinearRegressionAnalyzer()

    linRegAnaly.coef_ = np.array(tmp['coef'])
    linRegAnaly.intercept_ = np.array(tmp['intercept'])

    [x, _] = sql.fetch(mvid = mvid)
    tmp = np.array(x[0], dtype = np.float32)
    x = np.log10(tmp + np.ones(tmp.shape))
    return linRegAnaly.predict(x)[0]

def main():
    if args.mode in ['l', 'learn']:
        learn()
    elif args.mode in ['x', 'examine']:
        for mp in args.modelfile:
            print(examine(modelpath = mp))
    else:
        print(analyze(args.mvid))

if __name__ == '__main__':
    main()
