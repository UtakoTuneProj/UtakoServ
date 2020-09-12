from utako.api.cloud_tasks import CloudTasksSender
import base64

class UtakoDelegateSender:
    queue = None
    endpoint = None
    method = 'POST'

    def __init__(self):
        if (self.class_queue_id is None) or (self.class_endpoint is None):
            raise NotImplementedError('queue and endpoint required')

        self.sender = CloudTasksSender(
            self.class_queue_id,
            self.class_endpoint,
            self.class_http_method
        )

    @property
    def class_queue_id(self):
        return self.queue

    @property
    def class_endpoint(self):
        return self.endpoint

    @property
    def class_http_method(self):
        return self.method

    def send(self, *params, **kwparams):
        payload = self.create_payloads(*params, **kwparams)
        self.sender.send(payload)

    def create_payloads(self, *params, **kwparams):
        raise NotImplementedError

class UtakoDelegateReceiver:
    def receive(self, data):
        raise NotImplementedError