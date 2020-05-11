import os

bind = ['0.0.0.0:' + str(os.getenv('PORT', 8193))]
proc_name = 'Utako-Job-Flask'
workers = 1
timeout = 300