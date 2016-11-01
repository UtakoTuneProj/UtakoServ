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

    score = []
    for cell in chart:
        x = ChartData(cell[-1])
        score.append(x.vocaran)
    score.sort()

    x = np.array(score)
    y = np.arange(0,1,1/len(score))

    plt.plot(x,y)
    plt.xscale('log')
    plt.show()

if __name__ == '__main__':
    main()
