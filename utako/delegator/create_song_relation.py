import utako.common_import as common
from utako.delegator.abstract_delegator import UtakoDelegateSender, UtakoDelegateReceiver
from utako.presenter.song_relation_constructor import SongRelationConstructor

class CreateSongRelationSender(UtakoDelegateSender):
    queue = common.config['gcp']['TASK_CREATETREE_QUEUE']
    endpoint = '/trigger/recreate_song_relations/by_movie_id'

    def create_payloads(self, movie_id):
        return {
            'movie_id': movie_id,
        }

class CreateSongRelationReceiver(UtakoDelegateReceiver):
    def receive(self, data):
        movie_id = data['movie_id']

        updater = SongRelationConstructor()
        return updater.recalculate_for(movie_id)
