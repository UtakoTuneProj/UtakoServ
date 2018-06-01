#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *

from .abstract_model import database, BaseModel
from .status import Status

class Chart(BaseModel):
    comment = IntegerField(db_column='Comment')
    id = ForeignKeyField(Status, db_column='ID')
    mylist = IntegerField(db_column='Mylist')
    time = FloatField(db_column='Time')
    view = IntegerField(db_column='View')
    epoch = IntegerField()

    class Meta:
        db_table = 'chart'
        indexes = (
            (('id', 'epoch'), True),
        )
        primary_key = CompositeKey('epoch', 'id')

