from utako.common_import import *
from utako.model.status import Status
from utako.delegator.song_score import SongScoreSender

class ScoreUpdater:
    def __call__(self, batch_size=50):
        target_mvs = Status.select(Status.id).where(
            ( Status.score_status == 1 )
            | (Status.score_status == None),
        )
        batch_count = ( ( len(target_mvs) - 1 ) // batch_size ) + 1

        for i in range(batch_count):
            movie_ids = tuple(map(lambda m: m.id, target_mvs[batch_size*i:batch_size*(i+1)]))
            SongScoreSender().send(
                movie_ids=movie_ids
            )

        return len(target_mvs)