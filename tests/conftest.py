import pytest

from utako.model.abstract_model import database
from utako.model.analyze_queue import AnalyzeQueue
from utako.model.chart import Chart
from utako.model.idtag import Idtag
from utako.model.status import Status
from utako.model.song_index import SongIndex
from utako.model.song_relation import SongRelation
from utako.model.status_song_relation import StatusSongRelation
from utako.model.tagcolor import Tagcolor
from utako.model.tagpair import Tagpair

@pytest.fixture()
def initialize_db():
    database.create_tables([
        AnalyzeQueue,
        Chart,
        Idtag,
        Status,
        SongIndex,
        SongRelation,
        StatusSongRelation,
        Tagcolor,
        Tagpair,
    ])
