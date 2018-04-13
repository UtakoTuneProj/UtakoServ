#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *
from utako.common_import import config

if config['database_type']['dbtype'] == 'mysql':
    database_class = MySQLDatabase
elif config['database_type']['dbtype'] == 'postgres':
    database_class = PostgresqlDatabase
elif config['database_type']['dbtype'] == 'sqlite':
    database_class = SqliteDatabase

database = database_class(**config['database'])

class UnknownField(object):
    def __init__(self, *_, **__): pass

class BaseModel(Model):
    class Meta:
        database = database

