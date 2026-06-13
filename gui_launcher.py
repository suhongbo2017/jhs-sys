import threading
import time
import urllib.request
import webview
from waitress import serve
from new_main import app

HOST = '127.0.0.1'
PORT = 5000
BASE_URL = f'http://{HOST}:{PORT}'


def start_flask():
    """在后台线程启动 Flask 服务器"""
    print("正在启动后台服务器...")
    serve(app, host=HOST, port=PORT, threads=6)


def wait_for_server(timeout=10):
    """等待服务器就绪（最多等待 timeout 秒）"""
    for i in range(timeout):
        try:
            with urllib.request.urlopen(f'{BASE_URL}/', timeout=3):
                print("服务器已就绪")
                return True
        except Exception:
            if i < timeout - 1:
                time.sleep(1)
    print("警告：服务器未在预期时间内启动")
    return False


def main():
    # 1. 启动 Flask 线程
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # 2. 等待服务器就绪
    wait_for_server()

    # 3. 创建并启动 webview 窗口
    print("正在打开桌面窗口...")
    window = webview.create_window(
        title='JHS System 桌面客户端',
        url=BASE_URL,
        width=1200,
        height=800,
        min_size=(800, 600),
        resizable=True,
        confirm_close=True,
    )
    webview.start(debug=False)


if __name__ == '__main__':
    main()