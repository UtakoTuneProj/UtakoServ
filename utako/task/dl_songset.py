#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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

pg = ProgressBar()

def dl_songset(limit = 5000):
    movies = Status.select(
        Status.id
    ).where(
        Status.score > 100
    ).limit(limit)

    ndl = NicoDownloader()
    for mvid in pg( movies ):
        try:
            tags = XmlReader()(mvid.id)['tags']
        except Exception:
            continue
        if not TAG_BLACKLIST.intersection(tags):
            ndl(mvid.id, writepath='songset/')
    WavNpyConverter()()
