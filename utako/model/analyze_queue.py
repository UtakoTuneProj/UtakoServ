#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *

from utako.model.abstract_model import database, BaseModel
from .status import Status

class AnalyzeQueue(BaseModel):
    id = AutoField(primary_key = True)
    movie_id = ForeignKeyField(Status, db_column='movie_id')
    version = IntegerField()
    status = IntegerField()
    queued_date = DateTimeField()

    class Meta:
        db_table = 'analyze_queue'
