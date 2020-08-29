#!/usr/bin/env python3
import time

from flask import Flask, request
import yaml

import utako
import logging

app = Flask(__name__)

class InvalidRequestBodyError(Exception):
    def __init__(self, message):
        self.message = message

def validate_request(request_body, required=[]):
    if not isinstance(request_body, dict):
        err_msg = 'Invalid request body'
    else:
        for key in required:
            if not key in request_body:
                err_msg = 'Missing required param {} '.format(key)
        else:
            err_msg = None

    if err_msg:
        raise InvalidRequestBodyError(err_msg)

@app.route('/')
def index():
    return "STATUS: OK"

@app.route('/log')
def logger_test():
    app.logger.info('Hello, logging.')
    return "Log sent"

@app.route('/trigger/test', methods=['POST'])
def trigger_test():
    data = request.get_json()

    import json
    print(json.dumps(data))
    app.logger.info(data)

    try:
        validate_request(data, ['text'])
    except InvalidRequestBodyError as e:
        app.logger.warning(e.message)
        return {'status': 'error', 'message': e.message}, 400

    return {'status': 'ok'}

@app.route('/trigger/analyze_by_count', methods=['POST'])
def analyze(movie_id):
    count = request.args.get('count', 1, type=int)
    utako.presenter.song_index_updater.SongIndexUpdater()(limit = count)
    return {
        'status': 'complete'
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
    data = request.get_json()

    try:
        validate_request(data)
    except InvalidRequestBodyError as e:
        app.logger.warning(e.message)
        return {'status': 'error', 'message': e.message}, 400

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