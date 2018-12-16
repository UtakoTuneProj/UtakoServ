from utako.common_import import *
from utako.model.status import Status
from utako.presenter.song_score_updater import SongScoreUpdater

class ScoreUpdater:
    def __call__(self):
        target_mvs = Status.select(Status.id).where(
            ( Status.score_status == 1 )
            | (Status.score_status == None),
        )

        target_ids = [m.id for m in target_mvs]
        SongScoreUpdater().update(*target_ids)
