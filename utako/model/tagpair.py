#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from peewee import *

from utako.model.abstract_model import database, BaseModel

class Tagpair(BaseModel):
    count = BigIntegerField()
    objective = CharField()
    subjective = CharField()

    class Meta:
        db_table = 'tagPair'
        primary_key = False

