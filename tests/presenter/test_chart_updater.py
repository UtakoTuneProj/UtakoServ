import pytest
import datetime

from utako.model.status import Status
from utako.model.chart import Chart
from utako.presenter.chart_updater import ChartUpdater

@pytest.fixture
def create_data(initialize_db):
    Status.insert_many([[
        'sm1', 0, 0, 1, None,
        datetime.datetime.now() - datetime.timedelta(minutes = 30)
        # first retrieved
    ],[
        'sm2', 1, 0, 1, None,
        datetime.datetime.now() - datetime.timedelta(minutes = 90)
        # second epoch
    ],[
        'sm3', 23, 0, 1, None,
        datetime.datetime.now() - datetime.timedelta(hours=23, minutes = 30)
        # on the post day last epoch
    ],[
        'sm4', 24, 0, 1, None,
        datetime.datetime.now() - datetime.timedelta(days=1, minutes = 30)
        # after a day, do not track until a week passed
    ],[
        'sm5', 24, 0, 1, None,
        datetime.datetime.now() - datetime.timedelta(days=6, hours=23, minutes = 30)
        # after a day, do not track until a week passed
    ],[
        'sm6', 24, 0, 1, None,
        datetime.datetime.now() - datetime.timedelta(days=7, minutes = 30)
        # last track, passed a week
    ],[
        'sm7', 25, 1, 1, None,
        datetime.datetime.now() - datetime.timedelta(days=7, hours=1, minutes = 30)
        # after a week, the movie will not be tracked
    ]], fields=[
        Status.id,
        Status.epoch,
        Status.iscomplete,
        Status.validity,
        Status.analyzegroup,
        Status.postdate,
    ]).execute()
    yield
    Status.delete().execute()

def test_chart_updater(initialize_db, create_data):
    ChartUpdater()()

