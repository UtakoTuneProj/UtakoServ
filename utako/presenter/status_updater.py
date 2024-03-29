#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.model.abstract_model import database
from utako.model.status import Status
from utako.presenter.json_reader import JsonReader
from utako.presenter.timedate_converter import TimedateConverter

class StatusUpdater:
    def __call__(self, limit = 15): #ランキング取得・キュー生成部

        inserted_data = []

        for i in range(limit): #15ページ目まで取得する
            self._rankfilereq(page = i)
            raw_rank = JsonReader()("tmp/ranking/" + str(i) + ".json")['data']

            inserted_data.extend([{
                'id':           movie['contentId'],
                'validity':     1,
                'epoch':        0,
                'iscomplete':   0,
                'postdate':     TimedateConverter().nico2datetime(movie['startTime']),
                'analyzegroup': None,
            } for movie in raw_rank ])

        with database.atomic():
            inserted_row_counts = Status.insert_many(inserted_data).on_conflict_ignore().execute()

        for j in range(i+1):
            os.remove("tmp/ranking/" + str(j) + ".json")

        map_func = lambda x: {
            'id': x.id,
            'postdate': x.postdate.strftime('%Y-%m-%dT%H:%M:%S')
        }

        return {'inserted_row_counts': inserted_row_counts}

    def _rankfilereq(
        self,
        searchtag="VOCALOID",
        limit=100,
        page=0
    ):
        '''
        searchtagに指定したタグのランキングを取得、指定のない場合はVOCALOIDタグ
        '''

        search_endpoint="https://snapshot.search.nicovideo.jp/api/v2/snapshot/video/contents/search" + \
                "?q={}".format(urllib.parse.quote(searchtag)) + \
                "&targets=tags" + \
                "&fields=contentId,title,tags,categoryTags,viewCounter,mylistCounter,commentCounter,startTime" + \
                "&_sort=-startTime" + \
                "&_offset={}".format(page*limit) + \
                "&_limit={}".format(limit) + \
                "&_context=UtakoOrihara(VocaloidRankingBot)"

        request = urllib.request.Request(
                    url=search_endpoint,
                    headers={
                        "User-Agent": "UtakoTuneProject",
                    },
                    method="GET",
                )

        try:
            with urllib.request.urlopen(request) as response:
                with open("tmp/ranking/" + str(page) + ".json", mode="wb") as f:
                    f.write(response.read())

        except urllib.error.URLError:
            print("Search query for",searchtag,"is failed. Maybe overloaded.")

        return None
