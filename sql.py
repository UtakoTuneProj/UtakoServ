# coding: utf-8
# SQL core module
import MySQLdb
import configparser

cnfp = configparser.ConfigParser()
cnfp.read('.auth.conf')

connection = MySQLdb.connect(**cnfp['DEFAULT'])
cursor = connection.cursor()
