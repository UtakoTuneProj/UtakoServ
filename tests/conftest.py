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

MODELS = [
    AnalyzeQueue,
    Chart,
    Idtag,
    Status,
    SongIndex,
    SongRelation,
    StatusSongRelation,
    Tagcolor,
    Tagpair,
]

@pytest.fixture(autouse=True)
def initialize_db():
    database.create_tables(MODELS)
    yield
    database.drop_tables(MODELS)

@pytest.fixture()
def inject_status():
    def _inject(
        records,
        fields=[
            Status.id,
            Status.epoch,
            Status.iscomplete,
            Status.validity,
            Status.analyzegroup,
            Status.postdate,
        ]):
        Status.insert_many(records, fields).execute()
    return _inject

@pytest.fixture()
def inject_chart():
    def _inject(
        records,
        fields=[
            Chart.status,
            Chart.epoch,
            Chart.time,
            Chart.view,
            Chart.comment,
            Chart.mylist,
        ]):
        Chart.insert_many(records, fields).execute()
    return _inject

@pytest.fixture()
def inject_mock_rankfilereq(monkeypatch):
    from utako.presenter.status_updater import StatusUpdater
    def _mock_rankfilereq(searchtag="VOCALOID", page=0):
        import shutil
        shutil.copy(
            'tests/mockfiles/rankings/{}.json'.format(page),
            'tmp/ranking/{}.json'.format(page)
        )
    monkeypatch.setattr(StatusUpdater, '_rankfilereq', _mock_rankfilereq)

@pytest.fixture()
def inject_mock_getthumbinfo(monkeypatch):
    from utako.presenter.xml_reader import XmlReader
    def _mock_getthumbinfo(self, mvid):
        from xml.etree import ElementTree
        with open('tests/mockfiles/thumbinfo/sm98765432.xml'.format(mvid)) as f:
            root = ElementTree.parse(f).getroot()
        return root
    monkeypatch.setattr(
        XmlReader,
        '_fetch_thumb_root',
        _mock_getthumbinfo
    )

@pytest.fixture()
def inject_mock_cloudtask(monkeypatch):
    from google.cloud.tasks_v2 import CloudTasksClient, CreateTaskRequest

    def _mock_cloudtask(self, request, *args):
        assert isinstance(request, CreateTaskRequest)

    def _mock_init(self, *args, **kwargs):
        pass

    monkeypatch.setattr(
        CloudTasksClient,
        '__init__',
        _mock_init
    )

    monkeypatch.setattr(
        CloudTasksClient,
        'create_task',
        _mock_cloudtask
    )

@pytest.fixture()
def inject_mock_cloudbucket(monkeypatch):
    from google.cloud.storage.client import Client as GCSclient

    class MockBucket():
        def __init__(self, name):
            self.name = name
        def blob(self, filename):
            return MockBlob(filename)

    class MockBlob():
        def __init__(self, name):
            self.name = name
        def exists(self):
            return False
        def upload_from_file(self, f):
            return
        def download_to_file(self, f):
            return

    monkeypatch.setattr(
        GCSclient,
        '__init__',
        lambda _s, _n: None
    )

    monkeypatch.setattr(
        GCSclient,
        'get_bucket',
        lambda _s, name: MockBucket(name)
    )

@pytest.fixture()
def inject_mock_movie_deleted_exception(monkeypatch):
    import yt_dlp

    def _mock_throw_error(self, movie_ids):
        raise yt_dlp.utils.DownloadError('削除された')

    monkeypatch.setattr(
        yt_dlp.YoutubeDL,
        'download',
        _mock_throw_error
    )