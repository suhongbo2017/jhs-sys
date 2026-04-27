import multiprocessing
import os # 导入 os 模块

# 绑定的IP和端口
bind = "0.0.0.0:8080"

# 工作进程数
# 建议根据应用程序的性质（CPU密集型 vs. I/O密集型）、服务器的CPU核心数和可用内存进行性能测试以优化此值。
workers = multiprocessing.cpu_count() * 2 + 1

# 工作模式
# 对于I/O密集型或需要更高并发的应用程序，可以考虑使用异步工作模式，例如 "gevent" 或 "eventlet"。
# 这需要安装相应的库（例如 pip install gevent）。
worker_class = "sync"

# 最大客户端并发数量
worker_connections = 1000

# 进程名称
proc_name = "gunicorn_jhs_system"

# 超时时间
# 根据应用程序的实际需求调整此值。对于长时间运行的任务，可以考虑使用异步任务队列来处理。
timeout = 30

# 访问日志文件 (使用绝对路径)
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True) # 确保日志目录存在
accesslog = os.path.join(log_dir, "gunicorn_access.log")

# 错误日志文件 (使用绝对路径)
errorlog = os.path.join(log_dir, "gunicorn_error.log")

# 日志级别
loglevel = "info"
