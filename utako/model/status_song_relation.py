from peewee import *

from .abstract_model import database, BaseModel
from .status import Status
from .song_relation import SongRelation

class StatusSongRelation(models.Model):
    id = AutoField()
    status = ForeignKey(Status, on_delete = CASCADE)
    song_relation = ForeignKey(SongRelation, on_delete = CASCADE)

    class Meta:
        db_table = 'status_song_relation'

