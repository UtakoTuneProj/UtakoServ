from datetime import datetime
from datetime import timedelta
import pytest
import freezegun

from utako.presenter.chart_updater import ChartUpdater

from utako.model.chart import Chart
from utako.model.status import Status

NOW = datetime.now()

class CaptiveChartUpdater:
    @freezegun.freeze_time(NOW)
    @pytest.mark.parametrize(
        'status_data,expect_to_insert_chart,expected_validity',[
        ([  # first retrieved
            'sm98765432', 0, 0, 1, None,
            NOW - timedelta(hours=0)
        ],  True, True),

        ([  # first retrieved (with delay margin)
            'sm98765432', 0, 0, 1, None,
            NOW - timedelta(hours=1, minutes=30)
        ],  True, True),

        ([  # first retrieved (over delay margin)
            'sm98765432', 0, 0, 1, None,
            NOW - timedelta(hours=1, minutes=30, seconds=1)
        ],  True, True),

        ([  # too early update
            'sm98765432', 23, 0, 1, None,
            NOW - timedelta(hours=23, seconds=-1)
        ],  True, True),

        ([  # last epoch at postday
            'sm98765432', 23, 0, 1, None,
            NOW - timedelta(hours=23)
        ],  True, True),

        ([  # after a day
            'sm98765432', 24, 0, 1, None,
            NOW - timedelta(hours=24)
        ],  False, True),

        ([  # before a week
            'sm98765432', 24, 0, 1, None,
            NOW - timedelta(days=7, hours=1, seconds=-1)
        ],  False, True),

        ([  # update on after a week
            'sm98765432', 24, 0, 1, None,
            NOW - timedelta(days=7, hours=1)
        ],  True, True),

        ([  # update on after a week (with delay margin)
            'sm98765432', 24, 0, 1, None,
            NOW - timedelta(days=7, hours=2, minutes=30)
        ],  True, True),

        ([  # too late for update on after a week
            'sm98765432', 24, 0, 1, None,
            NOW - timedelta(days=7, hours=2, minutes=30, seconds=1)
        ],  True, True),
        ])
    def should_insert_chart_record_from_thumb(
        self,
        inject_mock_getthumbinfo,
        inject_status,
        status_data,
        expect_to_insert_chart,
        expected_validity,
    ):
        inject_status([status_data])

        ChartUpdater()()
        assert Chart.select().exists() == expect_to_insert_chart

        status_record = Status.select().first()
        expected_epoch = status_data[1] + int(expect_to_insert_chart)
        expected_iscomplete = (( expected_epoch == 25 ) and expected_validity )

        assert status_record.validity == expected_validity
        assert status_record.epoch == expected_epoch
        assert status_record.iscomplete == expected_iscomplete
        assert ( status_record.analyzegroup is None ) ^ expected_iscomplete
