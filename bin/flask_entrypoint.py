#!/usr/bin/env python3
import time
import json
import logging
from functools import wraps

from flask import Flask, request
import yaml

import utako
from utako.delegator.song_analyze import SongAnalyzeReceiver
from utako.delegator.create_song_relation import CreateSongRelationReceiver
from utako.delegator.song_score import SongScoreReceiver

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
            if len(required) != 0:
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

@app.route('/trigger/analyze/by_movie_id', methods=['POST'])
@validate_request(['movie_id', 'model_version'])
def analyze_by_movie_id(data):
    job = SongAnalyzeReceiver()
    status = job.receive(data, host=request.host)

    if status in ['succeeded', 'skipped', 'deleted', 'redirect']:
        return {
            'status': 'complete',
            'job_result': status
        }
    else:
        return {
            'status': 'failure',
            'job_result': status
        }, 504

@app.route('/trigger/recreate_song_relations/by_movie_id', methods=['POST'])
@validate_request(['movie_id'])
def recreate_song_relations_by_movie_id(data):
    job = CreateSongRelationReceiver()
    count = job.receive(data)

    return {
        'status': 'complete',
        'inserted_relations': count
    }

@app.route('/trigger/hourly', methods=['POST'])
def hourly():
    task_result = utako.task.check_chart.check_chart()
    return {
        'status': 'complete',
        'result': task_result,
    }

@app.route('/trigger/daily', methods=['POST'])
def daily():
    task_result = utako.task.check_status.check_status()
    return {
        'status': 'complete',
        'result': task_result,
    }

@app.route('/trigger/update_song_score', methods=['POST'])
def update_song_score():
    sent_movies = utako.task.update_song_score.update_song_score()
    return {
        'status': 'complete',
        'result': sent_movies,
    }

@app.route('/worker/score', methods=['POST'])
@validate_request(['movie_ids'])
def song_score_worker(data):
    job = SongScoreReceiver()
    result = job.receive(data)
    return {
        'status': 'complete',
        'result': result,
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
    app.logger = utako.root_logger
    app.run(host="127.0.0.1", port=8193, debug=True)
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
