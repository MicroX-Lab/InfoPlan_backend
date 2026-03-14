# encoding: utf-8
"""Gunicorn 生产部署配置"""
import multiprocessing
import os

# 绑定地址
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:5001")

# Worker 配置（2C4G 服务器推荐 2-3 workers）
workers = int(os.getenv("GUNICORN_WORKERS", min(2, multiprocessing.cpu_count())))
worker_class = "sync"
threads = 2

# 超时
timeout = 120
graceful_timeout = 30

# 日志
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# 进程名
proc_name = "infoplan-backend"

# 预加载应用（节省内存）
preload_app = True
