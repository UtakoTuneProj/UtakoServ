#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import utako

if __name__ == '__main__':
    utako.task.hourly.hourly()

    try:
        main()
    except Exception as e:
        logger.error(e)
    else:
        endTime = datetime.datetime.now()
        logger.info(
            'Utako Task successfully finished. Exec Time: {}'
            .format(endTime - startTime)
        )
