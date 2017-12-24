#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *

from utako.model.abstract_model import database, BaseModel

class Tagcolor(BaseModel):
    color = IntegerField()
    tagname = CharField(db_column='tagName')
    value = IntegerField()

    class Meta:
        db_table = 'tagColor'
        indexes = (
            (('tagname', 'color'), True),
        )
        primary_key = CompositeKey('color', 'tagname')

