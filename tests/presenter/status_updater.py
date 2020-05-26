import pytest

from utako.presenter.status_updater import StatusUpdater
from utako.model.status import Status

class CaptiveStatusUpdater:
    @pytest.mark.parametrize(
        'limit,status_count', [
            (2, 4),
            (4, 8),
    ])
    def should_update_status_from_rankfile(
        initialize_db,
        inject_mock_rankfilereq,
        limit,
        status_count
    ):
        StatusUpdater()(limit=limit)
        assert len(Status.select()) == status_count
