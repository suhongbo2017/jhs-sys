# JHS System 交接文档

> 更新时间：2026-11-16 ｜ 维护人：suhongbo ｜ 仓库：`D:\VSCODE\PYTHON3\system`（GitHub: suhongbo2017/jhs-sys）

---

## 1. 项目是什么

金蝶（Kingdee K3）送货单/物料查询与打印系统，Flask Web 应用，供车间/业务人员在浏览器中按送货单号查询明细并调用各客户专属打印模板打印标签。

- **技术栈**：Python 3.11 + Flask 2.3 + pandas + pyodbc（SQL Server）+ Bootstrap-Flask 2.2；Windows 生产用 Waitress，Linux/Docker 用 Gunicorn
- **部署形态**：① 服务器上 `wsgi.py`（Waitress，端口 8080）+ PM2 守护（`manage.bat`）；② Docker（`Dockerfile` + `docker-compose.yml`）；③ 桌面客户端 `gui_launcher.py`（pywebview 窗口，开发用）
- **数据库**：
  - 金蝶 2019 账套：SQL Server `192.168.0.234`，库 `AIS20191210135722`（schema 常量 `DB_SCHEMA_2019`）
  - 金蝶 2023 账套：同服务器，`AIS20230525154804`（仅 LSM 物料查询用）
  - MySQL `192.168.0.118` / `material_table`：`write_mysql.py` 用（**当前业务未使用**，勿随意启用，见 §6）

## 2. 功能与路由速查

| 路由 | 功能 | codeName | 说明 |
|---|---|---|---|
| `/` | 主页卡片导航 | - | `templates/index.html` |
| `/yunHaiPrint` | 云海打印 | 1 | `_PRINT_ROUTES` 动态注册 |
| `/jinLiPrint` | 金力打印 | 2 | |
| `/jiuMaoPrint` | 久茂打印 | 3 | |
| `/qianJi` | 千骥打印 | 4 | |
| `/tongtaiying` | 同泰盈打印 | 5 | |
| `/fengzhenchang` `/fengzhenchang_copy` | 丰振昌（两个版本） | 6 | copy 版更复杂，需定夺保留哪个 |
| `/zhidongli` | 智动力打印 | 2 | 独立处理函数，解析"整支规格" |
| `/queryMaterial` `/LSMqueryMaterial` | 物料查询 | - | LSM 查 2023 账套 |
| `/bartender_tag/` | Bartender 标签查询页 | - | `tag_code2026.html`（781 行单页应用） |
| `/date_tag/` | 月份标签设计器 | - | 独立静态模块 `date_tag/`，需求见 `date_tag/readme.txt` |
| `/qrcode` | 二维码生成 | - | |
| `/translate` | DeepLX 翻译 | - | |

**核心链路**：`new_main.py:process_delivery_data` → `server_connect.py:query_SEord(单号, codeName)` → 先查 `SEOutStock`（表头，取 FInterID）再查 `SEOutStockEntry`（明细）→ `ENTRY_CONFIGS[codeName]` 定义列名/SQL 字段/后处理聚合 → pandas DataFrame → 渲染打印模板。

**输入约定**：多单号用 `/` 分隔（如 `JHS028203/JHS0282024`），自动转大写。

## 3. 关键文件

```
new_main.py            # Flask 主应用：应用工厂、路由、打印模板处理（唯一维护点）
server_connect.py      # 数据库查询：连接、ENTRY_CONFIGS 配置驱动、物料查询
templates/base.html    # 全站布局（nav + 主题切换），本地化静态资源
templates/nav.html     # 顶部导航（各打印入口）
static/js/datatables.js  # 项目自己的 DataTables 初始化脚本（中文配置），不是库
logs/                  # app.log（UTF-8，RotatingFileHandler 10MB×5）
manage.bat             # PM2 管理菜单（启动/停止/日志/开机自启），解释器为 .venv\Scripts\pythonw.exe
.env                   # 本地配置（已 gitignore，勿提交）；加载逻辑 new_main.py:_load_env_file()
```

## 4. 2026-11-16 审核与修复记录（重要）

### 已修复（本机已验证）
1. **单号不存在时整页 500** → `process_delivery_data` 空结果提前返回，用户输错单号现在得到"未查询到数据"提示（原日志反复出现 `No objects to concatenate`）
2. **qrcode.html DOM XSS** → `innerHTML` 改为 `createElement`/`textContent`
3. **异常细节泄露** → 页面只显示"操作出错，详情请查看服务日志"，堆栈仅进日志
4. **日志乱码** → RotatingFileHandler 加 `encoding='utf-8'`；旧 GBK 日志轮转为 `logs/app.log.gbk-bak-20261116`
5. **CDN 全部本地化** → jQuery/DataTables/bootstrap-icons/qrcode 库已下载到 `static/`，断外网可用；`base.html` 加了 favicon（复用 `static/img/LOGO英文原文件.ico`）
6. **依赖双源统一** → `pyproject.toml` 为唯一真源（范围覆盖生产实测版本），`requirements.txt` 改为生产 `.venv` 锁定版本，去掉了 7 个无代码引用的包；`uv.lock` 已重新生成
7. **Docker 修复** → ODBC 驱动自适应（优先 Driver 18/17，Windows 回退 `SQL Server`，行为不变）；`Dockerfile` 改 `pip install .`；新增 `.env` + 零依赖加载器（SECRET_KEY 固定，不再重启丢 flash）
8. **Git 卫生** → `logs/app.log`、`__pycache__/*.pyc` 已 `git rm --cached`

### ⚠️ 未提交！
上述改动（9 个修改 + 6 个新静态文件 + 3 个索引删除）**尚未 commit**，接手第一件事：
```bash
git add -A && git commit -m "fix(P0/P1): 空单号500/XSS/日志UTF-8；CDN本地化、依赖统一、Docker驱动、.env加载"
```

### 有意不做的事（决策记录）
- **数据库密码硬编码 `server_connect.py`（`Jhs16888`）+ sa 账号**：业务确认内网使用，暂不改。但注意：密码已进 Git 历史且 README 指向公开 GitHub 仓库，**若仓库公开/泄露，必须改 sa 密码**（改密后同步 `.env`）。代码已支持 `DB_PASSWORD` 环境变量覆盖。

## 5. 快速验证方法（改代码后必跑）

```bash
cd /d/VSCODE/PYTHON3/system
.venv/Scripts/python.exe -c "
import sys,werkzeug;sys.path.insert(0,'.'); werkzeug.__version__='3.1.3'
import new_main
c=new_main.app.test_client()
routes=['/','/qrcode','/date_tag/','/date_tag_view','/bartender_tag/','/queryMaterial','/LSMqueryMaterial','/translate','/yunHaiPrint','/jinLiPrint','/jiuMaoPrint','/qianJi','/tongtaiying','/fengzhenchang','/fengzhenchang_copy','/zhidongli']
print({p: c.get(p).status_code for p in routes})
"
```
全部 200 即通过（真实数据库查询需内网环境）。

## 6. 已知问题与待办（P2，按优先级）

1. **生产副本漂移**：`C:\Users\Administrator\pi-cwd-20260603\system` 是旧快照（停在 2026-05-09 的 bc387a9）。确认生产实际运行目录，旧副本应删除或拉齐，否则"改了代码没生效"的事故会重演
2. **模板布局两套写法**：14 个模板用 `{% include 'base.html' %}`（输出两套 `<html>`），只有 `qrcode.html`/`date_tag_view.html` 用正规 `{% extends %}` —— 后续改版建议统一
3. **打印模板字体未统一**：`jiuMaoPrint.html:41` 仍 SimSun，`jinLiPrint.html` 无 font-family（上次"统一 YaHei"未覆盖）
4. **无测试/CI**：§5 冒烟脚本可固化为 pytest；`server_connect.py` 的聚合后处理是纯函数，适合单测
5. **死文件清理**：`5s.html`、`2024-01-02.html`(5907行)、`Scheduled_Tasks.html`、`query_seorder.html`、`qianJi222.html`、`testNav.html` 无路由引用；`write_mysql.py` 的 `if_exists='replace'` 会删表重建，启用前务必确认
6. **性能**：每单号新建数据库连接（无池），多单号循环 N 次；可加 3~5 连接小池 + 表头明细合并为一条 JOIN SQL
7. **智动力"生产日期"解析**：`new_main.py:_parse_spec_string` 相关注释掉的猜测逻辑，需向使用方确认规则
8. **`fengzhenchang_copy`** 与 `fengzhenchang` 是同客户两版本，需定夺

## 7. 坑与注意事项

- **验证脚本里 `werkzeug.__version__='3.1.3'`** 是因为 Flask 2.3.2 的 test_client 会读 `werkzeug.__version__`（Werkzeug 3 已删除该属性），生产运行不受影响
- 日志中文乱码的历史数据：2026-11-16 之前的 `app.log` 是 GBK，读旧段会解码失败
- `Dockerfile` 用 msodbcsql18，要求连接走 Driver 18 + `TrustServerCertificate=yes`（代码已自适应）
- `docker-compose.yml` 依赖 `.env`，机器上必须有该文件
- PM2 用 `pythonw.exe` 跑 `wsgi.py`（无窗口），看日志用 `manage.bat` 选项 5
- 主页/导航里两个外链：云盘 `http://192.168.30.1:5212`、工具箱 `http://192.168.30.1:8031`（别删，是业务入口）
- `templates/index.html` 等使用 `{% include 'base.html' %}`，block 内容渲染在 `</html>` 之后——浏览器能正常显示，但不是标准结构（见待办 2）
- `date_tag/` 是独立静态模块（自带 Dockerfile/compose），通过 `send_from_directory` 服务，改它不要动 Flask 模板

## 8. 环境速记

| 项 | 值 |
|---|---|
| 生产端口 | 8080（wsgi.py / gunicorn），开发 5000 |
| SQL Server | 192.168.0.234，账套 2019 主用、2023 仅 LSM |
| MySQL | 192.168.0.118 / material_table（未启用） |
| Python venv | `.venv`（uv 管理，`uv sync` 安装） |
| 日志 | `logs/app.log` UTF-8，10MB×5 轮转 |
| 打包 | `pyinstaller.txt`：`pyinstaller --name wsgi --onefile --windowed --add-data "static;static" --add-data "templates;templates" wsgi.py` |
