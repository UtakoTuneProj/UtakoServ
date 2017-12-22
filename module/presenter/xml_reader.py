#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import utako.common_import

from utako.model.chart import Chart
from utako.exception.mov_deleted_exception import MovDeletedException

class XmlReader:
    def __call__(self, fp, coding = 'utf-8'):
        with codecs.open(fp, 'r', coding) as f:
            root = ET.parse(f).getroot()
        if root.attrib['status'] == 'fail':
            raise MovDeletedException('{} is deleted data.'.format(fp))

        for child in root[0]:#xmlの辞書化
            if child.tag == 'tags':
                setattr(self, 'tags', [x.text for x in child])
            elif child.tag in ["mylist_counter", "comment_num", "view_counter"]:#一部を数値に変換
                setattr(self, child.tag, int(child.text))
            elif child.tag == 'first_retrieve':
                self.first_retrieve = Time(stream = child.text, mode = 'nico')
            else:
                setattr(self, child.tag, child.text)

        # http://www.lifewithpython.com/2014/08/python-use-multiple-separators-to-split-strings.html
        self.title_split = [x for x in re.split("[/\[\]【】\u3000〔〕／〈〉《》［］『』「」≪≫＜＞]",self.title) if len(x) > 0] #指定文字でタイトルを分割

        return None

