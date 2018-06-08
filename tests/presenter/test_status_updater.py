import shutil
import pytest

from utako.presenter.status_updater import StatusUpdater

@pytest.fixture
def create_data(initialize_db):
    pass

def test_status_updater_call(monkeypatch, initialize_db, create_data):
    def mockreturn(searchtag="VOCALOID", page=0):
        shutil.copy(
            'tests/mockfiles/ranking.{}.json'.format(page),
            'tmp/ranking/{}.json'.format(page)
        )
    monkeypatch.setattr(StatusUpdater, '_rankfilereq', mockreturn)
    StatusUpdater()()
