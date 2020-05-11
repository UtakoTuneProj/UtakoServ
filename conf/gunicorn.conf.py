import os

bind = ['127.0.0.1:' + str(os.getenv('PORT', 8193))]
proc_name = 'Utako-Job-Flask'
workers = 1
timeout = 300