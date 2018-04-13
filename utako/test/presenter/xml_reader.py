#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
import yaml
from utako.presenter.xml_reader import XmlReader
from utako.exception.mov_deleted_exception import MovDeletedException

class TestXmlReader(unittest.TestCase):
    testcase_ok = (
        # xml file path, dict
        (
            'utako/test/resources/ok_01.xml',
            yaml.load(open('utako/test/resources/ok_01.yaml')),
        ),
    )
    testcase_fail = (
        # xml file path, exception class
        (
            'utako/test/resources/fail_01.xml',
            MovDeletedException,
        ),
    )
    def test_call(self):
        for arg, res in self.testcase_ok:
            self.assertEqual(XmlReader()(arg), res)

        for arg, exc in self.testcase_fail:
            self.assertRaises(exc, XmlReader(), arg)
