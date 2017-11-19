# -*-coding: utf-8-*-
import sqlalchemy as alch
import configparser

cnfp = configparser.ConfigParser()
cnfp.read('.auth.conf')

engine = alch.engine_from_config(cnfp['alch'], prefix = 'alch.')
metadata = alch.MetaData(bind = engine, reflect = True)

fetch = metadata.tables['status'].select().execute().fetchall()
for c in fetch:
    print(c)
print(len(fetch))
