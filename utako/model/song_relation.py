from peewee import *

from .abstract_model import database, BaseModel

class SongRelation(BaseModel):
    id = AutoField()
    distance = IntegerField()
    version = IntegerField()

    class Meta:
        db_table = 'song_relation'

