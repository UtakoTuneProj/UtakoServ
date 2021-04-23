import utako.common_import as common
from utako.api.cloud_tasks import CloudTasksSender
from utako.delegator.abstract_delegator import UtakoDelegateSender, UtakoDelegateReceiver
from utako.delegator.create_song_relation import CreateSongRelationSender
from utako.presenter.song_index_updater import SongIndexUpdater

class SongAnalyzeSender(UtakoDelegateSender):
    queue = common.config['gcp']['TASK_ANALYZE_QUEUE']
    endpoint = '/trigger/analyze/by_movie_id'

    def __init__(self):
        super().__init__()
        self.sender = CloudTasksSender(
            queue=self.class_queue_id,
            endpoint=self.class_endpoint,
            method=self.class_http_method,
            task_host=common.config['gcp']['TASK_ANALYZE_URL']
        )

    def create_payloads(self, movie_id, model_version=common.settings['model_version']):
        return {
            'movie_id': movie_id,
            'model_version': model_version
        }

class SongAnalyzeReceiver(UtakoDelegateReceiver):
    def receive(self, data, host=None):
        movie_id = data['movie_id']

        if host is not None and host != common.config['gcp']['TASK_ANALYZE_URL']:
            SongAnalyzeSender().send(movie_id=data['movie_id'])
            return 'redirect'

        updater = SongIndexUpdater()
        result  = updater.index_by_movie_ids([movie_id])

        for status in result:
            if result[status]:
                job_result = status

        if job_result == 'succeeded':
            CreateSongRelationSender().send(movie_id)

        return job_result
