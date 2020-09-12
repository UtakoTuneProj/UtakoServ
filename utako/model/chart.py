#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *

from .abstract_model import database, BaseModel
from .status import Status

class Chart(BaseModel):
    id = AutoField()
    comment = IntegerField(db_column='Comment')
    status = ForeignKeyField(Status, db_column='status_id')
    mylist = IntegerField(db_column='Mylist')
    time = FloatField(db_column='Time')
    view = IntegerField(db_column='View')
    epoch = IntegerField()

    class Meta:
        db_table = 'chart'
        indexes = (
            (('status_id', 'epoch'), True),
        )

