#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from utako.common_import import *

from utako.model.chart import Chart
from utako.model.status import Status
from utako.model.idtag import Idtag
from utako.presenter.xml_reader import XmlReader
from utako.exception.no_response_exception import NoResponseException
from utako.exception.mov_deleted_exception import MovDeletedException

class ChartUpdater:

    def __call__(self):
    #statusDBを読みチャートを更新

        todays_mv = Status.select().where(
            Status.postdate
            > datetime.datetime.now()
            - datetime.timedelta(days = 1),
            Status.validity == 1
        ).execute()

        lastwks_mv = Status.select().where(
            Status.postdate
            < datetime.datetime.now()
            - datetime.timedelta(days=7, hours=1),
            Status.validity == 1,
            Status.iscomplete == 0
        ).execute()

        for query in todays_mv:
            self._update(query)
        for query in lastwks_mv:
            self._update(query)

        return None

    def _update(self, query):
        mvid = query.id
        epoch = query.epoch
        postdate = query.postdate

        while True:
            try:
                movf = XmlReader()(mvid)
            except NoResponseException:
                time.wait(5)
                continue
            except MovDeletedException:
                Status.update(
                    validity = False
                ).where(
                    Status.id == mvid
                ).execute()
                return None
            else:
                break

        passedmin = (
            datetime.datetime.now()
            - postdate
        ).total_seconds() / 60

        Chart.create(
            status_id = mvid,
            epoch     = epoch,
            time      = passedmin,
            view      = movf['view_counter'],
            comment   = movf['comment_num'],
            mylist    = movf['mylist_counter'],
        )

        isComplete = False
        status = True

        if epoch < 24:
            if passedmin < epoch*60 or ((epoch+1)*60 + 30 < passedmin):
                status = False
        elif epoch > 24:
            status = False
        elif passedmin < 10140 or 10200 + 30 < passedmin:
            status = False

        if status and epoch == 24:
            source = []
            for tag in movf['tags']:
                source.append({
                    'status_id' : mvid,
                    'tagname'   : tag,
                    'count'     : 1
                })

            Idtag.insert_many(
                source
            )
            isComplete = True

        Status.update(
            validity = status,
            epoch = epoch + 1,
            iscomplete = isComplete,
            analyzegroup = random.randint(0,19) if isComplete else None
        ).where(
            Status.id == mvid
        ).execute()

        return None
