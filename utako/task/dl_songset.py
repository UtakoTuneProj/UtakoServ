#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path

from utako.common_import import *

from utako.model.status import Status
from utako.presenter.nico_downloader import NicoDownloader
from utako.presenter.xml_reader import XmlReader
from utako.presenter.wav_npy_converter import WavNpyConverter

TAG_BLACKLIST = {
    # 'MikuMikuDance',
    # 'MMD',
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

    dl_movies(filter_movies(movies), TAG_BLACKLIST)

    WavNpyConverter()(
        fetched_movies,
        songs_limit=songs_limit,
        length_limit=length_limit,
        sr=sr,
        length=length,
        duplication=duplication,
    )

def create_chronicle_songset(
    year,
    songs_limit=100,
    length_limit=200,
    sr=8192,
    length=65536,
    duplication=8,
    writepath='songset/',
):
    movies = Status.select(
        Status.id
    ).where(
        Status.postdate.year == year
    ).order_by(-Status.score).limit(songs_limit)

    filtered_movies = filter_movies(movies, TAG_BLACKLIST)
    dl_movies(filtered_movies, writepath)

    WavNpyConverter()(
        filtered_movies,
        songs_limit=songs_limit,
        length_limit=length_limit,
        sr=sr,
        length=length,
        duplication=duplication,
        dataset_basename='chronicle.{year}'.format(year=year),
    )

def filter_movies(movies_list, blacklist_tags):
    filtered_movies = []
    for mvid in movies_list:
        try:
            tags = XmlReader()(mvid.id)['tags']
        except Exception:
            continue
        if not blacklist_tags.intersection(tags):
            filtered_movies.append(mvid.id)
    return filtered_movies

def dl_movies(movies_list, writepath):
    ndl = NicoDownloader()
    for mvid in pg( movies_list ):
        if not ( Path(writepath) / 'wav' / (mvid + '.wav') ).is_file():
            ndl(mvid, writepath=writepath)
