#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.exception.mov_deleted_exception import MovDeletedException
from utako.exception.no_response_exception import NoResponseException
from utako.presenter.timedate_converter import TimedateConverter

class XmlReader:
    def __call__(self, mvid, coding = 'utf-8'):
        ret = {}

        req = urllib.request.Request("http://ext.nicovideo.jp/api/getthumbinfo/" + mvid)

        try:
            with urllib.request.urlopen(req) as f:
                root = ET.parse(f).getroot()
        except urllib.error.HTTPError:
            raise NoResponseException("Cannot get thumbs for {}".format(mvid))

        if root.attrib['status'] == 'fail':
            raise MovDeletedException('{} has been deleted.'.format(mvid))

        for child in root[0]:#xmlの辞書化
            if child.tag == 'tags':
                ret['tags'] = [x.text for x in child]
            elif child.tag in [
                "mylist_counter",
                "comment_num",
                "view_counter"
            ]:#一部を数値に変換
                ret[child.tag] = int(child.text)
            elif child.tag == 'first_retrieve':
                ret['first_retrieve'] = TimedateConverter().nico2datetime(child.text)
            else:
                ret[child.tag] = child.text

        # http://www.lifewithpython.com/2014/08/python-use-multiple-separators-to-split-strings.html
        ret['title_split'] = [x for x in re.split("[/\[\]【】\u3000〔〕／〈〉《》［］『』「」≪≫＜＞]",ret['title']) if len(x) > 0] #指定文字でタイトルを分割

        return ret

