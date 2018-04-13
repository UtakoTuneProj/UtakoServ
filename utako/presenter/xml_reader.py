#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.model.chart import Chart
from utako.exception.mov_deleted_exception import MovDeletedException
from utako.presenter.timedate_converter import TimedateConverter

class XmlReader:
    def __call__(self, fp, coding = 'utf-8'):
        ret = {}

        with codecs.open(fp, 'r', coding) as f:
            root = ET.parse(f).getroot()
        if root.attrib['status'] == 'fail':
            raise MovDeletedException('{} is deleted data.'.format(fp))

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
                ret['first_retrieve'] = TimedateConverter()(child.text)
            else:
                ret[child.tag] = child.text

        # http://www.lifewithpython.com/2014/08/python-use-multiple-separators-to-split-strings.html
        ret['title_split'] = [x for x in re.split("[/\[\]【】\u3000〔〕／〈〉《》［］『』「」≪≫＜＞]",ret['title']) if len(x) > 0] #指定文字でタイトルを分割

        return ret

