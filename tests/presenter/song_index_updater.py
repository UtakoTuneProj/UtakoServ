import pytest
import datetime
import freezegun

from utako.presenter.song_index_updater import SongIndexUpdater
from utako.model.status import Status

NOW = datetime.datetime.now()

class CaptiveSongIndexUpdater:
    @freezegun.freeze_time(NOW)
    def should_mark_as_invalid_on_deleted(
        self,
        inject_status,
        inject_mock_movie_deleted_exception,
        inject_mock_cloudbucket
    ):
        inject_status([[
            'sm98765432', 0, 0, 1, None,
            NOW - datetime.timedelta(minutes=30)
        ]])

        result = SongIndexUpdater().index_by_movie_ids(['sm98765432'])
        assert len(result['deleted']) == 1
        assert result['deleted'][0] == 'sm98765432'

        status_record = Status.select().where(Status.id == 'sm98765432').first()
        assert status_record.validity == 0

    @freezegun.freeze_time(NOW)
    def should_skip_invalid_movies_by_default(
        self,
        inject_status,
    ):
        inject_status([[
            'sm98765432', 0, 0, 0, None,
            NOW - datetime.timedelta(minutes=30)
        ]])

        result = SongIndexUpdater().index_by_movie_ids(['sm98765432'])
        assert len(result['skipped']) == 1
        assert result['skipped'][0] == 'sm98765432'