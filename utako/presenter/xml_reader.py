#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.exception.mov_deleted_exception import MovDeletedException
from utako.exception.no_response_exception import NoResponseException
from utako.presenter.timedate_converter import TimedateConverter

class XmlReader:
    def __call__(self, mvid, coding = 'utf-8'):
        root = self._fetch_thumb_root(mvid)
        thumb_as_dict = self._parse_element_tree_to_dict(root)

        return thumb_as_dict


    def _fetch_thumb_root(self, mvid):
        request = urllib.request.Request(
            "http://ext.nicovideo.jp/api/getthumbinfo/" + mvid
        )

        try:
            with urllib.request.urlopen(request) as f:
                root = ET.parse(f).getroot()
        except urllib.error.HTTPError:
            raise NoResponseException("Cannot get thumbs for {}".format(mvid))

        if root.attrib['status'] == 'fail':
            raise MovDeletedException('{} has been deleted.'.format(mvid))

        return root


    def _parse_element_tree_to_dict(self, xml_root):
        as_dict = {}

        for child in xml_root[0]:#xmlの辞書化
            if child.tag == 'tags':
                as_dict['tags'] = [x.text for x in child]

            elif child.tag in [
                "mylist_counter",
                "comment_num",
                "view_counter"
            ]:#一部を数値に変換
                as_dict[child.tag] = int(child.text)

            elif child.tag == 'first_retrieve':
                as_dict['first_retrieve'] = TimedateConverter().nico2datetime(child.text)

            else:
                as_dict[child.tag] = child.text

        as_dict['title_split'] = self._split_title(as_dict['title'])

        return as_dict


    def _split_title(self, raw_title):
        # http://www.lifewithpython.com/2014/08/python-use-multiple-separators-to-split-strings.html
        return [x for x in re.split("[/\[\]【】\u3000〔〕／〈〉《》［］『』「」≪≫＜＞]", raw_title) if len(x) > 0] #指定文字でタイトルを分割