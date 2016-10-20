import UtakoServCore as core
import numpy as np
import matplotlib.pyplot as plt

class ChartData:
    def __init__(self,l):
        self.view = l[1]
        self.comment = l[2]
        self.mylist = l[3]

        self.cm_cor = (self.view + self.mylist) / (self.view + self.comment + self.mylist)
        self.vocaran = self.view + self.comment * self.cm_cor + self.mylist ** 2 / self.view * 2
        self.vt30 = self.view + self.comment * self.cm_cor + self.mylist * 20
        self.vocasan = self.view + self.comment * 8 + self.mylist * 25

def main():
    chartf = core.JSONfile('dat/chartlist_init.json')
    chart = chartf.read()

    vocaran = []
    # vt30 = []
    # vocasan = []
    for cell in chart:
        x = ChartData(cell[-1])
        vocaran.append(x.vocaran)
        # vt30.append(x.vt30)
        # vocasan.append(x.vocasan)
    vocaran.sort()
    # vt30.sort()
    # vocasan.sort()

    x1 = np.array(vocaran)
    # x2 = np.array(vt30)
    # x3 = np.array(vocasan)
    y = np.arange(0,1,1/len(vocaran))

    plt.plot(x1,y, label = 'vocaran')
    # plt.plot(x2,y, label = 'vt30')
    # plt.plot(x3,y, label = 'vocasan')
    plt.xscale('log')
    # plt.legend()
    plt.show()

if __name__ == '__main__':
    main()
