from peewee import *

from .abstract_model import database, BaseModel
from .status import Status
from .song_relation import SongRelation

class StatusSongRelation(BaseModel):
    id = AutoField()
    status = ForeignKeyField(Status, on_delete = 'CASCADE')
    song_relation = ForeignKeyField(SongRelation, on_delete = 'CASCADE')

    class Meta:
        db_table = 'status_song_relation'

