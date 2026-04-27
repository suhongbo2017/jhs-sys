from new_main import app

# Gunicorn 期望一个名为 'application' 的可调用对象
application = app

if __name__ == "__main__":
    from waitress import serve
    print("正在 Windows 上启动 Waitress 服务器 (端口 8080)...")
    serve(app, host='0.0.0.0', port=8080)
