#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import utako.common_import

from utako.exception.no_response_exception import NoResponseException

class XmlFetcher:
    def __call__(self, mvid, force = False): #動画情報xmlを取得
        fname = 'getthumb/' + mvid + '.xml'
        if not os.path.exists(fname):
            try:
                urllib.request.urlretrieve(
                    "http://ext.nicovideo.jp/api/getthumbinfo/" + mvid, fname
                )
            except:
                raise NoResponseException("Cannot get thumbs for {}".format(mvid))

        return None
