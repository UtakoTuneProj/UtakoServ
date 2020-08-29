import json
from google.cloud import pubsub_v1
import utako.common_import as common

class CloudPubSubSender:
    def __init__(self, topic_id):
        project_id = common.config['pubsub']['PROJECT_ID']
        topic_id = topic_id

        if project_id is None or topic_id is None:
            raise NotImplementedError

        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_id)

    def send(self, payload):
        data = json.dumps(payload).encode("utf-8")
        self.publisher.publish(self.topic_path, data=data)
