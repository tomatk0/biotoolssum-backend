import multiprocessing

timeout = 1200
workers = 2
bind = "unix:myproject.sock"
umask = 0o007
reload = True
capture_output = True
loglevel = "info"
errorlog = "/var/log/biotoolssum/gunicorn_error.log"
