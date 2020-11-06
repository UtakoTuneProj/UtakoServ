import utako.common_import as common
from utako.delegator.abstract_delegator import UtakoDelegateSender, UtakoDelegateReceiver
from utako.presenter.song_score_updater import SongScoreUpdater

class SongScoreSender(UtakoDelegateSender):
    queue = common.config['gcp']['TASK_SCORE_QUEUE']
    endpoint = '/worker/score'

    def create_payloads(self, movie_ids):
        return {
            'movie_ids': movie_ids,
        }

class SongScoreReceiver(UtakoDelegateReceiver):
    def receive(self, data):
        movie_ids = data['movie_ids']

        updater = SongScoreUpdater()
        return updater.update(*movie_ids)
