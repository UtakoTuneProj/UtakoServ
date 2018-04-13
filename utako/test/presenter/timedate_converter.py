#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import datetime
from utako.presenter.timedate_converter import TimedateConverter

class TestTimedateConverter(unittest.TestCase):
    now = datetime.datetime.now().replace(microsecond=0)
    testcase = (
    # nico-format, datetime
    ( now.strftime("%Y-%m-%dT%H:%M:%S+09:00"), now ),
    )

    def test_nico2datetime(self):
        for arg, res in self.testcase:
            self.assertEqual(TimedateConverter()(arg), res)

