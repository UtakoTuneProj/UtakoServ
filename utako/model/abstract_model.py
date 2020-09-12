#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import MySQLDatabase, SqliteDatabase, Model
from utako.common_import import config

dbtype = config['database_type']['dbtype']

if dbtype == 'mysql':
    database = MySQLDatabase(**config['database'])
elif dbtype == 'sqlite':
    database = SqliteDatabase(**config['database'])
else:
    raise TypeError('utako only supports mysql and sqlite')

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

