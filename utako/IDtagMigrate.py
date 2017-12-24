#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from common_import import *

import sql
cmdf = sql.cmdf

if __name__ == '__main__':
    db = sql.DataBase('tesuto')
    ittbl = sql.IDTagTable(db)

    mvlist = [
        os.path.basename(r).rsplit('.')[0] for r in glob.glob('getthumb/*')
    ]
    pb = ProgressBar(0, len(mvlist))

    for i, mvid in enumerate(mvlist):
        pb.update(i+1)
        try:
            f = cmdf.MovInfo(mvid)
            for tag in f.tags:
                q = {
                    'ID'        : mvid,
                    'tagName'   : tag,
                    'count'     : 1,
                }
                ittbl.set(**q)
        except cmdf.MovDeletedException:
            continue
        except:
            print(mvid, tag)
            raise

    db.commit()
