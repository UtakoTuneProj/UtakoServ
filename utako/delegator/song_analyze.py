import utako.common_import as common
from utako.delegator.abstract_delegator import UtakoDelegateSender, UtakoDelegateReceiver
from utako.presenter.song_index_updater import SongIndexUpdater

class SongAnalyzeSender(UtakoDelegateSender):
    queue = common.config['gcp']['TASK_ANALYZE_QUEUE']
    endpoint = '/trigger/analyze/by_movie_id'

    def create_payloads(self, movie_id, model_version=common.settings['model_version']):
        return {
            'movie_id': movie_id,
            'model_version': model_version
        }

class SongAnalyzeReceiver(UtakoDelegateReceiver):
    def receive(self, data):
        movie_id = data['movie_id']

        updater = SongIndexUpdater()
        result  = updater.index_by_movie_ids([movie_id])

        for status in result:
            if result[status]:
                return status
