#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *

from .abstract_model import database, BaseModel
from .status import Status

class Idtag(BaseModel):
    id = AutoField()
    status_id = ForeignKeyField(Status, db_column='status_id')
    count = IntegerField(null=True)
    tagname = CharField(db_column='tagName', index=True)

    class Meta:
        db_table = 'IDtag'
        indexes = (
            (('status_id', 'tagname'), True),
        )
        primary_key = id

