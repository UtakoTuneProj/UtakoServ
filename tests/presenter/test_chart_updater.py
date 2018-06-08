import pytest
import datetime

from utako.model.status import Status
from utako.model.chart import Chart
from utako.presenter.chart_updater import ChartUpdater

@pytest.fixture
def create_data(initialize_db):
    Status.insert_many([[
        'sm1', 1, 0, 1, None,
        datetime.datetime.now() - datetime.timedelta(minutes = 30)
    ],[
        'sm2', 2, 0, 1, None,
        datetime.datetime.now() - datetime.timedelta(minutes = 90)
    ],[
        'sm3', 23, 0, 1, None,
        datetime.datetime.now() - datetime.timedelta(hours=23, minutes = 30)
    ],[
        'sm4', 24, 0, 1, None,
        datetime.datetime.now() - datetime.timedelta(days=1, minutes = 30)
    ]], fields=[
        Status.id,
        Status.epoch,
        Status.iscomplete,
        Status.validity,
        Status.analyzegroup,
        Status.postdate,
    ]).execute()

def test_chart_updater(initialize_db, create_data):
    ChartUpdater()()

