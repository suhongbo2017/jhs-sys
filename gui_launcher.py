import os
import threading
import time
import webview
from waitress import serve
from app_client import app

def start_flask():
    """在后台线程启动 Flask 服务器"""
    print("正在启动后台服务器...")
    # 使用 waitress 提供生产环境级别的服务
    serve(app, host='127.0.0.1', port=5000, threads=6)

def main():
    # 1. 启动 Flask 线程
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # 2. 等待服务器启动（可选，webview 会自动重试）
    time.sleep(1)

    # 3. 创建并启动 webview 窗口
    print("正在打开桌面窗口...")
    window = webview.create_window(
        title='JHS System 桌面客户端',
        url='http://127.0.0.1:5000',
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        confirm_close=True
    )

    # 启动 GUI 事件循环
    webview.start(debug=False)

if __name__ == '__main__':
    main()
