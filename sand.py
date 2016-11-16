# -*-coding: utf-8-*-
import UtakoServCore as core
import matplotlib.pyplot as plt
import numpy as np

f = core.JSONfile('dat/tagstat.json')
print(len(f.data))
x = list(list(zip(*f.data))[2])
x.sort()
plt.plot(x, np.arange(len(x)) / len(x))
plt.xscale('log')
plt.show()
