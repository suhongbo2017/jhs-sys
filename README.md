# JHS System (金蝶系统查询应用)

## 项目简介
这是一个基于 Flask 的 Web 应用程序，用于查询金蝶数据库中的送货单和物料信息。它提供了多个路由来处理不同类型的查询和打印请求，并集成了日志记录和错误处理。

## 主要功能
- 查询金蝶数据库中的送货单表头和表体信息。
- 根据不同的 `codeName` 参数，对送货单明细进行不同的数据处理和汇总。
- 查询物料信息。
- 支持多条件物料查询。
- 集成翻译功能（通过 PyDeepLX）。
- 生产环境部署支持 Gunicorn。

## 安装指南

### 1. 克隆仓库
```bash
git clone https://github.com/suhongbo2017/jhs-sys.git
cd jhs-sys
```

### 2. 创建并激活虚拟环境
推荐使用 `uv` 或 `pip` 创建虚拟环境：
```bash
# 使用 uv (推荐)
uv venv
source .venv/bin/activate # Linux/macOS
.venv\Scripts\activate # Windows

# 或者使用 pip
python -m venv .venv
source .venv/bin/activate # Linux/macOS
.venv\Scripts\activate # Windows
```

### 3. 安装依赖
```bash
# 使用 uv (推荐)
uv sync

# 或者使用 pip
pip install -r requirements.txt # 如果有 requirements.txt
# 或者根据 pyproject.toml 安装
pip install ".[all]" # 如果 pyproject.toml 配置了可选依赖
pip install flask flask-bootstrap pandas pyodbc sqlalchemy waitress gunicorn mysql-connector-python PyDeepLX
```


```

## 运行指南

### 开发环境 (使用 Flask 内置服务器)
```bash
export FLASK_APP=new_main.py # Linux/macOS
$env:FLASK_APP="new_main.py" # Windows PowerShell
flask run --debug --host=0.0.0.0 --port=5000
```
然后访问 `http://localhost:5000`。

### 生产环境部署
由于项目可能在不同操作系统上运行，请根据您的系统选择合适的服务器：

#### Windows 系统 (使用 Waitress)
```bash
python wsgi.py
```
*注意：您需要确保 `wsgi.py` 中使用了 `waitress` 来启动应用（参见下文）。*

#### Linux/macOS 系统 (使用 Gunicorn)
```bash
gunicorn -c gunicorn.conf.py wsgi:application
```
Gunicorn 将在 `0.0.0.0:8080` 启动服务。

### 桌面客户端模式 (Desktop Client)
如果您希望像普通的 Windows 软件一样以窗口形式运行该程序，请使用桌面启动器：
```bash
python gui_launcher.py
```
**特点：**
- **窗口化运行**：无需打开浏览器，直接在独立窗口中操作。
- **零侵入**：桌面版通过 `app_client.py` 运行，完全不改动原始的 Web 逻辑文件 `new_main.py`。
- **自动驱动**：脚本会自动启动后台服务并展示界面。

## 项目结构
```
.
├── .python-version
├── app.spec
├── gunicorn.conf.py          # Gunicorn 配置文件
├── new_main.py               # Flask 应用程序主文件，包含路由和业务逻辑
├── pyinstaller.txt
├── pyproject.toml            # 项目依赖和元数据配置
├── README.md                 # 项目说明文档
├── server_connect.py         # 数据库连接和查询逻辑
├── uv.lock                   # uv 包管理器锁定文件
├── write_mysql.py            # MySQL 写入功能（目前大部分注释掉）
├── wsgi.py                   # WSGI 入口文件，用于 Gunicorn 部署
├── gui_launcher.py           # 桌面客户端启动器（用于窗口化运行）
├── app_client.py             # 桌面客户端专用后端逻辑（保持 Web 原文件不被改动）
├── YourAppName.spec
├── build/
├── dist/
├── logs/                     # 应用程序日志
├── static/                   # 静态文件 (CSS, JS, 图片等)
├── templates/                # HTML 模板文件
└── uploads/                  # 文件上传目录
```

## 许可证
[在此处添加您的许可证信息，例如 MIT 许可证]
