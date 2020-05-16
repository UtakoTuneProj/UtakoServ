#!/usr/bin/env python3
import time

from flask import Flask, request
import yaml

import utako
import logging

app = Flask(__name__)

@app.route('/')
def index():
    return "STATUS: OK"

@app.route('/log')
def logger_test():
    app.logger.info('Hello, logging.')
    return "Log sent"

@app.route('/trigger/analyze_by_count', methods=['POST'])
def analyze(movie_id):
    count = request.args.get('count', 1, type=int)
    utako.presenter.song_index_updater.SongIndexUpdater()(limit = count)
    return {
        'status': 'complete'
    }

@app.route('/trigger/hourly', methods=['POST'])
def hourly():
    utako.task.hourly.hourly()
    return {
        'status': 'complete'
    }

@app.route('/trigger/recreate_song_relations', methods=['POST'])
def recreate_song_relations():
    task = utako.presenter.song_relation_constructor.SongRelationConstructor()
    task(max_relations=13)
    return {
        'status': 'complete'
    }

