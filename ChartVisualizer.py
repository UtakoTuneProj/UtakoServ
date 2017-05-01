import ServCore as core
import numpy as np
import matplotlib.pyplot as plt

def main():
    chartf = core.JSONfile('dat/chartlist_init.json')
    chart = chartf.read()

    week = []
    holi = []
    for cell in chart:
        x = core.Chartcell(cell[-1])
        if cell[-2][0] in range(17,24):
            holi.append(x.vocaran)
        else:
            week.append(x.vocaran)
    week.sort()
    holi.sort()

    x1 = np.array(week)
    y1 = np.arange(0,1,1/len(x1))
    x2 = np.array(holi)
    y2 = np.arange(0,1,1/len(x2))

    plt.plot(x1,y1, label = 'other')
    plt.plot(x2,y2, label = 'Golden TIME')
    # plt.plot(x3,y, label = 'vocasan')
    plt.xscale('log')
    plt.legend()
    plt.show()

if __name__ == '__main__':
    main()
