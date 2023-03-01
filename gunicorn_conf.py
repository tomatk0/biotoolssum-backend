import multiprocessing

timeout = 1200
workers = multiprocessing.cpu_count() * 2 + 1
bind = 'unix:myproject.sock'
umask = 0o007
reload = True
capture_output = True
loglevel = 'debug'
accesslog = 'gunicorn_access.log'
errorlog = 'gunicorn_error.log'