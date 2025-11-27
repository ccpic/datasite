"""
Gunicorn 配置文件
适用于 Windows Server 2022 上的 Linux 容器
"""
import multiprocessing
import os

# 服务器配置
bind = "0.0.0.0:8000"
backlog = 2048

# 工作进程配置
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = os.environ.get('GUNICORN_WORKER_CLASS', 'sync')
worker_connections = int(os.environ.get('GUNICORN_WORKER_CONNECTIONS', 1000))
timeout = int(os.environ.get('GUNICORN_TIMEOUT', 120))
keepalive = int(os.environ.get('GUNICORN_KEEPALIVE', 5))

# 日志配置
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 进程命名
proc_name = 'datasite'

# 服务器钩子
def on_starting(server):
    server.log.info("Starting datasite application")

def on_reload(server):
    server.log.info("Reloading datasite application")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def pre_fork(server, worker):
    pass

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)

def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)

