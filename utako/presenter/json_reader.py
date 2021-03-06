#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

class JsonReader:
    def __call__(self, fp, coding = 'utf-8'):
        with codecs.open(fp, 'r', coding) as fobj:
            stream = json.load(fobj, encoding = coding)

        return stream

