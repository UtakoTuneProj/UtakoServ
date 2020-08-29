#!/usr/bin/env python3
import time

from flask import Flask, request
import yaml

import utako
import logging

app = Flask(__name__)

def validate_pubsub(func, required=[]):
    def wrapper(*args, **kwargs):
        envelope = request.get_json()
        if not envelope:
            err_msg = 'No Pub/Sub message'
        elif not ( isinstance(envelope, dict) ) or ( 'message' not in envelope ):
            err_msg = 'Invalid Pub/Sub message'
        else:
            for key in required:
                if not key in envelope:
                    err_msg = 'Missing required param {} '.format(key)
            else:
                err_msg = None

        if err_msg:
            app.logger.warning(err_msg)
            return {'status': 'error', 'message': err_msg}, 400

        return func(*args, **kwargs)
    return wrapper

@app.route('/')
def index():
    return "STATUS: OK"

@app.route('/log')
def logger_test():
    app.logger.info('Hello, logging.')
    return "Log sent"

@app.route('/trigger/test', methods=['POST'])
@validate_pubsub(['text'])
def trigger_test():
    request_body = request.get_json()

    app.logger.info(request_body['text'])
    print(request_body['text'])
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
@validate_pubsub
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