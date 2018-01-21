#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *
from utako.common_import import config

database = MySQLDatabase(**config['database'])

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

