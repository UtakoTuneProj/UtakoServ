#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *

from .abstract_model import database, BaseModel
from .status import Status

class SongIndex(BaseModel):
    id = ForeignKeyField(Status, db_column='ID')
    value0 = FloatField()
    value1 = FloatField()
    value2 = FloatField()
    value3 = FloatField()
    value4 = FloatField()
    value5 = FloatField()
    value6 = FloatField()
    value7 = FloatField()
    version = IntegerField()

    class Meta:
        db_table = 'song_index'
