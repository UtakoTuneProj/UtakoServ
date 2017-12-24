#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ServCore: core module for hourly task

import utako

from utako.presenter.chart_updater import ChartUpdater
from utako.presenter.status_updater import StatusUpdater

def main():
    StatusUpdater()()
    ChartUpdater()()

    return 0

# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='UTF-8')
if __name__ == '__main__':
    main()
