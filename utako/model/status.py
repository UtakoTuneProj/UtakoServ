#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *

from utako.model.abstract_model import database, BaseModel

class Status(BaseModel):
    id = CharField(db_column='ID', primary_key=True)
    analyzegroup = IntegerField(db_column='analyzeGroup', null=True)
    epoch = IntegerField()
    iscomplete = IntegerField(db_column='isComplete')
    postdate = DateTimeField(null=True)
    validity = IntegerField()
    score = FloatField(null=True)
    score_status = IntegerField(null=True)

    class Meta:
        db_table = 'status'

