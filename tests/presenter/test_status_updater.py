from utako.presenter.status_updater import StatusUpdater
from utako.model.status import Status

def test_status_updater_call(
    initialize_db,
    inject_mock_rankfilereq,
):
    StatusUpdater()(limit = 2)
    assert len(Status.select()) == 4
    StatusUpdater()(limit = 4)
    assert len(Status.select()) == 8
