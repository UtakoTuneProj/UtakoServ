import json
from google.cloud import tasks_v2
import utako.common_import as common

class CloudTasksSender:
    def __init__(self, queue, endpoint, method='POST'):
        self.project_id   = common.config['gcp']['PROJECT_ID']
        self.location     = common.config['gcp']['LOCATION']
        self.task_host    = common.config['gcp']['TASK_BASE_URL']
        self.task_account = common.config['gcp']['TASK_ACCOUNT']

        if any(map(lambda x: x is None, [
            self.project_id,
            self.location,
            self.task_host,
            self.task_account,
            queue,
            endpoint,
        ])):
            raise NotImplementedError

        if endpoint[0] is not '/':
            raise ValueError('endpoint must begin with slash')

        self.client = tasks_v2.CloudTasksClient()
        self.parent = self.client.queue_path(self.project_id, self.location, queue)
        self.url = self.task_host + endpoint
        self.method = method

    def send(self, payload):
        task = {
            'http_request': {
                'http_method': self.method,
                'url': self.url,
                'oidc_token': {
                    'service_account_email': self.task_account
                }
            }
        }

        if payload is not None:
            task['http_request']['body'] = json.dumps(payload).encode("utf-8")

        return self.client.create_task(self.parent, task)
