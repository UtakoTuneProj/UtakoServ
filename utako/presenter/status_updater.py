#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.model.status import Status
from utako.presenter.json_reader import JsonReader
from utako.presenter.timedate_converter import TimedateConverter

class StatusUpdater:
    def __call__(self): #ランキング取得・キュー生成部
        for i in range(15): #15ページ目まで取得する
            self._rankfilereq(page = i)
            raw_rank = JsonReader()("tmp/ranking/" + str(i) + ".json")['data']
            for mvdata in raw_rank:
                mvid = mvdata['contentId']
                postdate = TimedateConverter().nico2datetime(mvdata['startTime'])

                if len(Status.select().where(
                    Status.id == mvid
                )) == 0:
                    #取得済みリストの中に含まれていないならば
                    Status.create(
                        id          = mvid,
                        validity    = 1,
                        epoch       = 0,
                        iscomplete  = 0,
                        postdate    = postdate,
                        analyzegroup= None
                    )
                else:
                    break
            else:
                continue
            break

        for j in range(i+1):
            os.remove("tmp/ranking/" + str(j) + ".json")

        return None

    def _rankfilereq(self, searchtag = "VOCALOID", page = 0):
    #searchtagに指定したタグのランキングを取得、指定のない場合はVOCALOIDタグ
        rankreqbase="http://api.search.nicovideo.jp/api/v2/video/contents/search" + \
                    "?q={}".format(urllib.parse.quote(searchtag)) + \
                    "&targets=tags" + \
                    "&fields=contentId,title,tags,categoryTags,viewCounter,mylistCounter,commentCounter,startTime" + \
                    "&_sort=-startTime" + \
                    "&_offset={}".format(page*100) + \
                    "&_limit=100" + \
                    "&_context=UtakoOrihara(VocaloidRankingBot)"

        try:
            urllib.request.urlretrieve(rankreqbase, "tmp/ranking/" + str(page) + ".json")
        except urllib.error.URLError:
            print("Search query for",searchtag,"is failed. Maybe overloaded.")

        return None
