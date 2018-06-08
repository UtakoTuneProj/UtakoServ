#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *

from .abstract_model import database, BaseModel
from .status import Status

class Idtag(BaseModel):
    id = ForeignKeyField(Status, db_column='ID')
    count = IntegerField(null=True)
    tagname = CharField(db_column='tagName', index=True)

    class Meta:
        db_table = 'IDtag'
        indexes = (
            (('id', 'tagname'), True),
        )
        primary_key = CompositeKey('id', 'tagname')

