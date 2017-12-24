#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *

database = MySQLDatabase('***REMOVED***', **{'password': '***REMOVED***', 'user': '***REMOVED***', 'host': '***REMOVED***'})

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

