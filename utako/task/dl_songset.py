#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

from utako.common_import import *

from utako.model.status import Status
from utako.presenter.nico_downloader import NicoDownloader
from utako.presenter.xml_reader import XmlReader
from utako.presenter.wav_npy_converter import WavNpyConverter

TAG_BLACKLIST = {
    'MikuMikuDance',
    'MMD',
    'ボカロカラオケDB',
    'ニコカラ',
    '歌ってみた',
    'ニコニコカラオケDB',
    'VOCALOIDランキング',
    '演奏してみた',
    '日刊VOCALOIDランキング',
    '日刊トップテン！VOCALOID＆something',
    'VOCALOIDメドレー',
    'XFD',
    'クロスフェードデモ'
}

pg = tqdm

def dl_songset(
    writepath='songset/',
    songs_limit=1000,
    length_limit=100,
    sr=5513,
    length=8192,
    duplication=4,
    order_limit=50
):
    movies = Status.select(
        Status.id
    ).where(
        Status.score > order_limit
    ).order_by(-Status.postdate).limit(songs_limit)

    ndl = NicoDownloader()
    fetched_movies = []
    for mvid in pg( movies ):
        try:
            tags = XmlReader()(mvid.id)['tags']
        except Exception:
            continue
        if not TAG_BLACKLIST.intersection(tags):
            if not ( Path(writepath) / 'wav' / (mvid.id + '.wav') ).is_file():
                ndl(mvid.id, writepath=writepath)
            fetched_movies.append(mvid.id)
    WavNpyConverter()(
        fetched_movies,
        songs_limit=songs_limit,
        length_limit=length_limit,
        sr=sr,
        length=length,
        duplication=duplication,
    )
