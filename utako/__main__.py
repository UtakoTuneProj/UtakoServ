#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from utako.common_import import *
import utako.task.hourly

def entry_point():
    utako.task.hourly.hourly()

def main():
    argparser = argparse.ArgumentParser(
        description = "Utako Orihara: niconico VOCALOID movie analyzer"
    )
    argparser.add_argument('-v', '--verbosity',
        help = "Select debug level. "\
        + "-v CRITICAL-ERROR-WARNING-INFO-DEBUG -vvvvv",
        default = 3,
        action = 'count',
    )

    args = argparser.parse_args()
    logger.setLevel((6 - args.verbosity) * 10)

    logger.info('--------Utako Orihara: niconico VOCALOID movie analyzer--------')
    try:
        entry_point()
    except Exception as e:
        logger.critical(
            "Unexpected error occured. Program Stop...\n"\
            + "{}: {}"
            .format(type(e), e.args)
        )
        logger.exception(e)
        logger.info('--------Utako was crashed at {}.--------'.format(datetime.datetime.now()))
        raise
    else:
        logger.info('--------Utako was successfully closed at {}.--------'.format(datetime.datetime.now()))
        sys.exit(0)

main()
