import shutil
import pytest
import datetime

from utako.presenter.status_updater import StatusUpdater
from utako.model.status import Status

def test_status_updater_call(monkeypatch, initialize_db):
    def mock_rankfilereq(searchtag="VOCALOID", page=0):
        shutil.copy(
            'tests/mockfiles/ranking.{}.json'.format(page),
            'tmp/ranking/{}.json'.format(page)
        )
    monkeypatch.setattr(StatusUpdater, '_rankfilereq', mock_rankfilereq)
    StatusUpdater()(limit = 2)
    assert len(Status.select()) == 4
    StatusUpdater()(limit = 4)
    assert len(Status.select()) == 8
