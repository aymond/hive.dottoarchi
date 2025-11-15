# Gunicorn configuration file
# This file can be used with: gunicorn -c gunicorn.conf.py dot2archimate.web.app:app

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
threads = int(os.environ.get('GUNICORN_THREADS', 2))
timeout = 120
keepalive = 5

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.environ.get('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'dot2archimate'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if running gunicorn directly with SSL, otherwise use reverse proxy)
# keyfile = None
# certfile = None

# Performance tuning
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Graceful timeout
graceful_timeout = 30

