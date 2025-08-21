import multiprocessing

# 绑定的IP和端口
bind = "0.0.0.0:8080"

# 工作进程数
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
worker_class = "sync"

# 最大客户端并发数量
worker_connections = 1000

# 进程名称
proc_name = "gunicorn_jhs_system"

# 超时时间
timeout = 30

# 访问日志文件
accesslog = "logs/gunicorn_access.log"

# 错误日志文件
errorlog = "logs/gunicorn_error.log"

# 日志级别
loglevel = "info"