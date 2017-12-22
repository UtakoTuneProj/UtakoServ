#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *

from utako.model.abstract_model import database, BaseModel

class Idtag(BaseModel):
    id = CharField(db_column='ID')
    count = IntegerField(null=True)
    tagname = CharField(db_column='tagName', index=True)

    class Meta:
        db_table = 'IDtag'
        indexes = (
            (('id', 'tagname'), True),
        )
        primary_key = CompositeKey('id', 'tagname')

