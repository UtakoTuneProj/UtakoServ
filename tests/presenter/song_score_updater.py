import pytest
import datetime
import freezegun

from utako.presenter.song_score_updater import SongScoreUpdater
from utako.model.status import Status

NOW = datetime.datetime.now()

class CaptiveSongScoreUpdater:
    @freezegun.freeze_time(NOW)
    def should_update_status_score(
        self,
        initialize_db,
        inject_mock_getthumbinfo,
        inject_status,
        inject_chart,
    ):
        inject_status([[
            'sm98765432', 0, 0, 1, None,
            NOW - datetime.timedelta(minutes=30)
        ]])

        inject_chart([[
            'sm98765432', 0, 25, 334, 42, 42,
        ]])

        SongScoreUpdater().update(['sm98765432'])

        status_record = Status.select().where(Status.id == 'sm98765432').first()

        assert status_record.score is not None
        assert status_record.score_status == 1
