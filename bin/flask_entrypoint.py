#!/usr/bin/env python3
import time
import json
from functools import wraps

from flask import Flask, request
import yaml

import utako
import logging

app = Flask(__name__)

class InvalidRequestBodyError(Exception):
    def __init__(self, message):
        self.message = message

def validate_request(required=[]):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = json.loads(request.get_data(as_text=True))
            err_msg = None
            if len(required) is not 0:
                if not data:
                    err_msg = 'No message body'
                else:
                    for key in required:
                        if not key in data:
                            err_msg = 'Missing required param {} '.format(key)

            if err_msg:
                app.logger.warning(err_msg)
                return {'status': 'error', 'message': err_msg}, 400

            return func(data, *args, **kwargs)
        return wrapper
    return decorator

@app.route('/')
def index():
    return {'status': 'ok'}

@app.route('/log')
def logger_test():
    app.logger.info('Hello, logging.')
    return "Log sent"

@app.route('/trigger/test', methods=['POST'])
@validate_request(['text'])
def trigger_test(data):
    app.logger.debug(data['text'])
    return {'status': 'ok'}

@app.route('/trigger/analyze/by_count', methods=['POST'])
@validate_request(['count'])
def analyze_by_count(data):
    count = data['count']
    result = utako.presenter.song_index_updater.SongIndexUpdater()(limit = count)
    return {
        'status': 'complete',
        'result': result
    }

@app.route('/trigger/hourly', methods=['POST'])
def hourly():
    task_result = utako.task.check_status_chart.check_status_chart()
    return {
        'status': 'complete',
        'result': task_result,
    }

@app.route('/trigger/update_song_score', methods=['POST'])
def update_song_score():
    task_result = utako.task.update_song_score.update_song_score()
    return {
        'status': 'complete',
        'result': task_result,
    }

@app.route('/trigger/recreate_song_relations', methods=['POST'])
def recreate_song_relations():
    try:
        task = utako.presenter.song_relation_constructor.SongRelationConstructor()
        task(max_relations=13)
    finally:
        utako.model.abstract_model.database.close()

    return {
        'status': 'complete'
    }

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=8193, debug=True)
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers