#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Analyzer: UtakoChainer core module
import sys
import time
import argparse
import json

argparser = argparse.ArgumentParser(
description = "U.Orihara Tag Clasifier: tag clasifier for utako with k-means."
)
argparser.add_argument('-v', '--verbose',
help = "Select verbose level. "\
+ "1:CRITICAL | 2:ERROR | 3:WARNING(default) | 4:INFO | 5:DEBUG",
action = 'count',
default = 3,
# type = int,
# choices = range(1,6)
)
argparser.add_argument('-m', '--mode',
help  = "Select clasifier mode. " +\
        "l/learn : Clasify tags from database. (Default) | " +\
        "x/examine : Examine learned model. | " +\
        "a/analyze : Analyze specified Tag. -t param is needed. | " ,
type = str,
nargs = '?',
choices = ['l', 'x', 'a', 'learn', 'examine', 'analyze'],
default = 'l',
)
argparser.add_argument('-t', '--tag',
help = "Specify which tag to analyze. Use with -m a.",
type = str,
nargs = '?',
)

args = argparser.parse_args()

if __name__ == '__main__':
    print("importing modules...")

import numpy as np
import scipy as scp
try:
    import matplotlib.pyplot as plt
    GUI = True
except ImportError:
    GUI = False

import sql
cmdf = sql.cmdf

if __name__ == '__main__':
    print('imported modules')

def fetch(isTrain = False, mvid = None):
    if mvid == None and not isTrain:
        raise ValueError('Neither mvid nor isTrain was given.')

    db = sql.DataBase('test')
    ctbl = sql.ChartTable(db)
    ittbl = sql.IDTagTable(db)

    shapedInputs = []

    if isTrain:
        rawCharts = []

        print("Fetching from database...")
        for i in range(20):
            rawCharts.append(db.get(
                'select chart.* from chart join status using(ID) ' +
                'where status.analyzeGroup = %s and isComplete = 1 ' +
                'order by ID, epoch',
                [i]
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
                    shapedInputs[-1][-1].extend(cell[3:])
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

    fetchData = fetch(isTrain = True)
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
    f = fetch(isTrain = True)
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

def analyze(mvid, n_units = 200, layer = 20):
    with open(args.modelfile[0]) as f:
        tmp = json.load(f)

    linRegAnaly = LinearRegressionAnalyzer()

    linRegAnaly.coef_ = np.array(tmp['coef'])
    linRegAnaly.intercept_ = np.array(tmp['intercept'])

    [x, _] = fetch(mvid = mvid)
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
