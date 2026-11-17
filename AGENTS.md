# AGENTS.md — 给 AI Agent 的项目交接与工作手册

> 本文件是**面向 AI Agent 的唯一工作依据**（人类版见 `HANDOVER.md`）。
> 任何修改前先读完 §2 快速上手 与 §12 约定与陷阱。最后更新：2026-11-16。

---

## 1. 项目一句话

**金恒晟业务系统**：Flask 单体 Web 应用。核心业务是查金蝶（Kingdee K3）SQL Server 里的送货单/物料数据，按客户套用不同打印模板输出标签/送货单；附带 Bartender 字段查询、月份标签设计器、二维码生成、PDF/扫描件翻译。

- 仓库：`D:\VSCODE\PYTHON3\system`（GitHub `suhongbo2017/jhs-sys`，分支 `main`）
- 服务：Waitress 监听 **8080**，PM2 守护（`jhs-system`），生产地址 `http://192.168.100.17:8080`
- 使用者：车间/业务人员，**内网 Kubernetes 无关、单机部署**，无用户体系、无鉴权

---

## 2. 快速上手

```bash
cd /d/VSCODE/PYTHON3/system

# 装依赖（uv 为唯一包管理器，已有 .venv）
uv sync

# 启动（三选一）
.venv/Scripts/python.exe wsgi.py        # Waitress :8080（等价生产）
.venv/Scripts/python.exe new_main.py    # Flask debug :5000（热重载）
manage.bat                              # PM2 菜单（1 启动 / 5 日志）

# 改完必须跑冒烟（见 §11）
.venv/Scripts/python.exe -c "import sys,werkzeug;sys.path.insert(0,'.');werkzeug.__version__='3.1.3';import new_main;c=new_main.app.test_client();print([p+':'+str(c.get(p).status_code) for p in ['/','/queryMaterial','/pdf_translate']])"
```

**环境事实**：Python 3.11（`.python-version`）、venv 在 `.venv`、Node v22 + PM2 7.1.2 已装、Chrome 可用于无头截图自检。

---

## 3. 技术栈（精确、勿随意升级）

| 层 | 选型 | 版本约束 | 备注 |
|---|---|---|---|
| 语言/运行时 | Python | 3.11 | |
| Web 框架 | Flask | `>=2.3.3,<4` | **锁上限**，venv 实测 2.3.2 跑通；升级 3.x 需回归测试 |
| UI 扩展 | Bootstrap-Flask | `>=2.2.0` | 代码里 `from flask_bootstrap import Bootstrap4`，只用于注入 bootstrap，**不依赖其模板** |
| 数据 | pandas | `>=2.2` | 明细后处理/聚合/打印渲染 |
| 数据库驱动 | pyodbc | `>=4.0.39` | SQL Server；驱动**自适应**（见 §7） |
| ORM | SQLAlchemy | `>=2.0.17` | 仅 `write_mysql.py` 用（业务未启用） |
| 生产服务器 | waitress | `>=3.0.0` | Windows 生产；`wsgi.py` |
| 生产服务器 | gunicorn | `>=21.2.0` | Linux/Docker |
| PDF 翻译 | pymupdf `>=1.24` + pillow `>=10` | | 视觉大模型链路，无第三方 SDK |
| 桌面壳 | pywebview | `>=4.3.2` | `gui_launcher.py`，仅开发用 |
| 打包 | pyinstaller | `>=6.7.0` | 见 `pyinstaller.txt` |
| 进程守护 | PM2 (Node) | 7.1.2 | Windows；Linux 用 gunicorn + systemd |

**依赖唯一真源**：`pyproject.toml` + `uv.lock`。`requirements.txt` 是**生产 venv 的实测锁定副本**，改依赖顺序：改 `pyproject.toml` → `uv lock` → 验证 → 同步 `requirements.txt`。
**已移除**：PyDeepLX（旧文本翻译）、pdfplumber/reportlab/python-docx 等一票未用包。

---

## 4. 目录结构与职责

```
new_main.py               # ★ 应用唯一入口：应用工厂、全部路由、打印模板统一处理、.env 加载
server_connect.py         # ★ 数据层：连接、ENTRY_CONFIGS（codeName 驱动）、物料查询
pdf_translate_jobs.py     # ★ PDF 翻译后台任务（内存任务表 + 线程 + 产物扫描）
pdftranslate/             #  vendored PDF 翻译引擎（pipeline/vision/build/build_html/render/snap/textlayer/split/models…）
models.json               #  视觉模型注册表（qwen/gemini/openai/glm），可增删
templates/
  base.html               # ★ 全站骨架（app-shell：侧栏 + 主区 + 页脚），定义所有 block
  nav.html                # ★ 左侧功能栏 + 打印模板飞出面板 + 主题切换脚本
  index.html              #  工作台（pastel 卡片 + 卡片即时搜索）
  queryMaterial.html      #  物料查询（搜索胶囊 + table-card + 结果区提示）
  LSMqueryMaterial.html   #  同上（2023 账套）
  {yunHai,jinLi,jiuMao,qianJi,tongtaiying,fengzhenchang,fengzhenchang_copy,zhidongli}.html  # 打印模板
  pdf_translate.html      #  PDF 翻译（拖拽上传 + 轮询进度 + 产物下载）
  bartender_tag 实际名→ tag_code2026.html   # Bartender 字段表（自带 350 行样式 + 桥接层）
  date_tag_view.html      #  月份标签设计器外壳（iframe /date_tag/）
  qrcode.html / error.html
static/
  css/theme.css           # ★ 全站唯一视觉真源（设计令牌 + 组件 + 深浅色 + 打印安全区）
  css/base.css            #  历史遗留（导航/卡片旧样式 + @page 打印设置），仍被加载
  css/print.css           #  打印字号覆盖
  css/bootstrap.min.css, css/jquery.dataTables.min.css, css/bootstrap-icons.min.css
  js/jquery.min.js, js/jquery.dataTables.min.js, js/datatables.js(项目自己的初始化), js/bootstrap.bundle.min.js, js/qrcode.min.js, js/print.js
  fonts/bootstrap-icons.woff(2)   # 图标字体（路径已在 CSS 内改为 ../fonts/）
  img/                    # LOGO、favicon（LOGO英文原文件.ico）
date_tag/                 # 独立静态模块（月份标签设计器）：index.html/css/js + 自己的 Dockerfile
logs/                     # app.log（UTF-8，10MB×5 轮转）；git 忽略
uploads/pdf_translate/<job_id>/{in,out}   # PDF 翻译工作区；git 忽略
manage.bat                # PM2 菜单 + 环境自检/自动安装（★ 必须 CRLF）
wsgi.py / gunicorn.conf.py / Dockerfile / docker-compose.yml / pyinstaller.txt
HANDOVER.md（人类） AGENTS.md（本文件）
```

---

## 5. 核心数据流

### 5.1 送货单打印
```
浏览器 POST /yunHaiPrint  inputEntry="JHS0282102/JHS0282033"
  → new_main.handle_print_request(request, codeName, template)
    → process_delivery_data(data, code_name)
         data.upper().split('/')  → 逐单号 query_SEord(ds, code_name)
         ↓ 空结果安全返回 (None, None)：android 注意 concat([]) 会抛 ValueError，已有守卫
    → server_connect.query_SEord
         SELECT FInterID FROM SEOutStock WHERE FBILLNO=?      （表头）
         SELECT <sql_fields> FROM SEOutStockEntry WHERE FInterID=?  （明细）
         → DataFrame(columns=ENTRY_CONFIGS[cn].columns)
         → post_process(df)（聚合/类型转换）
    → render_template(template, table=df.to_dict('records'), data=seout_id)
```

### 5.2 物料查询
`POST /queryMaterial` → `process_material_query`（支持 `名/规格` 双条件）→ `server_connect.queryMaterial|LSMqueryMaterial` → `render_template(..., datas=df.iterrows())`；无结果时传 `message=`（**不用 flash**，见 §12）。

### 5.3 PDF 翻译
```
POST /pdf_translate (multipart, files[])
  → pdf_translate_jobs.create_job()          校验类型/大小 → 存 uploads/.../in → 起线程
    → pdftranslate.pipeline.run_job(files, Config.from_env(model), Options(...), out_dir, emit, progress)
        每页：文本层路由(auto) → 原生电子版走 translate_text（本地、免费）
                              → 扫描件走 vision.transcribe_page（视觉模型）
        → build_bilingual_pdf / build_html / write_markdown
  → 302 → /pdf_translate?job=<id>
前端每 1.5s GET /pdf_translate/status/<id> → 进度/日志/产物
下载 GET /pdf_translate/download/<id>/<name>  （有路径穿越防护）
```

---

## 6. 路由清单（21 条，除静态外）

| 路径 | 方法 | 端点 | 模板 | 说明 |
|---|---|---|---|---|
| `/` | GET | index | index.html | 工作台 |
| `/queryMaterial` | GET,POST | queryMaterial | queryMaterial.html | 2019 账套物料 |
| `/LSMqueryMaterial` | GET,POST | LSMqueryMaterial | LSMqueryMaterial.html | 2023 账套（铝塑膜） |
| `/yunHaiPrint` | GET,POST | yunHaiPrint | yunHaiPrint.html | codeName=1 云海 |
| `/jinLiPrint` | GET,POST | jinLiPrint | jinLiPrint.html | codeName=2 金力 |
| `/jiuMaoPrint` | GET,POST | jiuMaoPrint | jiuMaoPrint.html | codeName=3 九茂 |
| `/qianJi` | GET,POST | qianJi | qianJi.html | codeName=4 千骥 |
| `/tongtaiying` | GET,POST | tongtaiying | tongtaiying.html | codeName=5 同泰盈 |
| `/fengzhenchang` | GET,POST | fengzhenchang | fengzhenchang.html | codeName=6 丰正昌 |
| `/fengzhenchang_copy` | GET,POST | fengzhenchang_copy | fengzhenchang_copy.html | codeName=6 丰正昌第二版（待定夺保留哪个） |
| `/zhidongli` | GET,POST | zhidongli | zhidongli.html | codeName=2 + 规格拆解 |
| `/bartender_tag/` | GET | bartender_tag | tag_code2026.html | Bartender 字段表 |
| `/date_tag/` `/date_tag/<path>` | GET | date_tag / date_tag_static | — | 静态模块（send_from_directory） |
| `/date_tag_view` | GET | date_tag_view | date_tag_view.html | 设计器外壳（iframe） |
| `/qrcode` | GET | show_qrcode | qrcode.html | 二维码 |
| `/pdf_translate` | GET,POST | pdf_translate | pdf_translate.html | PDF 翻译主页面 |
| `/pdf_translate/status/<job_id>` | GET | pdf_translate_status | — | JSON 进度 |
| `/pdf_translate/download/<job_id>/<path:name>` | GET | pdf_translate_download | — | 产物下载（附件） |

打印路由由 `_PRINT_ROUTES` 表驱动动态注册（**加模板只改这张表**），统一经 `@handle_errors` + `handle_print_request`。

---

## 7. 数据层

```python
# server_connect.py
server   = os.getenv('DB_SERVER',  '192.168.0.234')
database = os.getenv('DB_DATABASE','AIS20191210135722')      # 2019 账套
username = os.getenv('DB_USERNAME','sa')
password = os.getenv('DB_PASSWORD','Jhs16888')               # 内网确认不改；已被 git 历史记录
DB_SCHEMA_2019 = f"{database}.dbo"
DB_SCHEMA_2023 = os.getenv('DB_SCHEMA_2023','AIS20230525154804.dbo')
```

- **ODBC 驱动自适应**（勿写死）：候选 `ODBC Driver 18 for SQL Server` → `17` → `SQL Server`（Windows 自带）；命中 18 时自动追加 `TrustServerCertificate=yes;`。连接串各段**必须带结尾分号**（曾因漏分号导致全站 01S00 报错）。
- **无连接池**：`get_connection()` 每次新建，`with` 块管理。多单号会 N 次连接（已知性能点，优化方向见 §13）。
- **SQL 全部参数化**，禁止字符串拼接用户输入。
- **codeName 语义**（`ENTRY_CONFIGS`）：1 云海聚合 / 2 金力含批次号 / 3 客户单号+数值转换 / 4 千骥规格拼接聚合 / 5、6 同泰盈+丰正昌（数值转换）。新增客户＝新增 EntryConfig 项 + `_PRINT_ROUTES` 行 + 模板。
- 物料查询走 `t_ICItemCore ⋈ t_ICItemBase ⋈ t_MeasureUnit`，`LIKE %q%`。

---

## 8. UI 设计系统（改样式必读）

### 8.1 风格定义
**轻盈柔和的企业级浅蓝质感**：浅蓝渐变底 + 柔和光晕、深藏青标题、大圆角、低饱和马卡龙卡片、圆形渐变图标徽标、胶囊按钮、柔和多层投影、左侧带文字的功能栏。深色模式为同构暗色令牌。

### 8.2 设计令牌（`static/css/theme.css` `:root`，**唯一配色来源**）
```css
--ink:#1b2559  --ink-2:#2f3d6d  --muted:#8b95b3  --muted-2:#a8b1c9
--line:#eef2fb --line-2:#e4ebf9
--blue:#3b6ef5 --blue-600:#2f5fe0 --blue-100:#e9efff --sky:#93c5fd
--surface:#fff --surface-2:#fbfdff  --page-1:#eaf2fe --page-2:#f5f9ff --page-3:#eef4fd
--r-xl:28px --r-lg:22px --r-md:16px --r-sm:12px --r-pill:999px
--sh-card / --sh-soft / --sh-pill / --sh-blue     /* 四级投影 */
--rail-w:198px                                    /* 侧栏宽度，窄屏 76px */
```
深色覆盖：`[data-bs-theme="dark"] { … }`。**禁止在模板里写死色值**，用 `var(--…)`。

### 8.3 组件类名（直接用，勿造新轮子）
| 类名 | 用途 |
|---|---|
| `.app-shell` / `.app-main` / `.app-content` | 骨架（margin-left 已按 `--rail-w` 让位） |
| `.side-rail` `.rail-brand` `.rail-logo` `.rail-brand-text` `.rail-nav` `.rail-item` `.rail-sep` `.rail-caret` `.rail-foot` `.rail-flyout` | 左侧功能栏；`.rail-item` 内含 `<i>` + `<span>` 文字；`data-match="/a,/b"` 控制高亮，`data-label` 供窄屏悬浮提示 |
| `.top-bar` `.page-head`(`h1`+`.sub`) `.page-title` `.top-actions` `.chip` `.icon-btn` | 页头区 |
| `.soft-card` / `.soft-card-flush` | 白底大圆角内容卡（标准容器） |
| `.pastel-card` + `.pastel-{peach,lav,sky,mint,rose,amber,violet}` | 首页马卡龙卡片（自带 hover 浮起） |
| `.badge-icon` + `.badge-{blue,orange,teal,rose,amber,violet,indigo}` | 76px 圆形渐变图标徽标 |
| `.card-title-mod` `.card-desc-mod` | 卡片标题/描述 |
| `.btn-pill` / `.btn-pill-primary` / `.btn-pill-ghost` / `.btn-pill-block` | 胶囊按钮（`.btn-pill` 白底，`.btn-pill-primary` 蓝渐变） |
| `.search-pill`（内含 `input` + 可放 `.btn-pill`） | 搜索胶囊（首页搜索、查询输入都用它） |
| `.table-card` + `table.dataTable`（样式已全局覆盖）、`.table-modern` | 表格容器与表格皮肤（DataTables 分页/搜索框已美化） |
| `.alert.alert-{warning,danger,info,success}` | 提示条（已软化成圆角无边框） |

### 8.4 布局骨架（`base.html`）
```
body
 └ .app-shell
    ├ {% include "nav.html" %}          → aside.side-rail（fixed，198px）
    └ main.app-main
        ├ {% block topbar %}            → .top-bar（页标题 + 右侧 chip/按钮）
        ├ .app-content
        │   ├ flash 渲染区（自动）
        │   ├ {% block input %}         → 查询页顶部输入区
        │   ├ {% block queryRow %}      → 打印模板的查询条
        │   ├ {% block container %}     → 主内容
        │   └ {% block map %}
        └ {% block footer %}            → 版权
 {% block scripts %}                    → 页面脚本（放在 body 末尾）
```

### 8.5 响应式
- `<1200px`：侧栏收为 76px 纯图标，恢复悬浮名称提示
- `<768px`：侧栏变顶部横向导航（只图标），`.app-main` 去左边距
- 栅格：`.card-grid` 用 `repeat(auto-fill, minmax(258px,1fr))`

### 8.6 打印约束（**改动最易出事**）
- 打印页纸张尺寸/字号由模板内 `<style>` 与 `print.css` 控制（如 210mm×148mm landscape、`@page`），**不要动这些数值**
- `.d-print-none` 在 `@media print` 下隐藏；侧栏/页头/页脚已在 print 媒体查询里隐藏
- 纸张预览容器 `.preview-container` 的圆角/阴影只在屏幕生效（打印走 `visibility:hidden` 方案，见模板内 `@media print`）—— 改样式后务必真机打印一次或用 Chrome「打印预览」核对分页

---

## 9. 模板编写规范（硬性）

1. **必须 `{% extends "base.html" %}`**。历史上有 14 个文件用 `{% include 'base.html' %}`，会把内容渲染到 `</html>` 之后（已全部修掉，不要再写回）。
2. `<style>` 放 `{% block head %}`，脚本放 `{% block scripts %}`，内容放对应 block。**block 外不得有可见内容**（extends 模式下会被丢弃）。
3. 静态资源用**绝对路径** `/static/...`（旧模板里的 `../static/...` 已改）。
4. **禁止引入外网 CDN**：jQuery / DataTables / Bootstrap / bootstrap-icons / qrcodejs 全部已本地化到 `static/`。内网断外网是硬要求。
5. 提示信息两种方式，按场景选：
   - **页面级**（系统错误、权限、上传失败）→ `flash(msg, 'warning'|'error'|'info')`，由 base.html 渲染在内容区顶部
   - **结果区级**（查询无结果、格式错误）→ 传 `message=` 变量，模板在结果卡片内渲染 `<div class="alert alert-warning">`（参考 `queryMaterial.html`）
6. 异常处理：路由用 `@handle_errors` 或自带 try/except，**对外只给通用文案**（"操作出错，详情请查看服务日志"），`logger.error(..., exc_info=True)` 记完整堆栈。
7. GET 直接访问页面**不得弹提示**（如"请输入查询内容"）；只有 POST 才提示。

---

## 10. PDF 翻译模块

- **引擎**：`pdftranslate/`（vendored 自 `D:\PI\pdftranslate`，上游 commit `fbab977`）。纯 stdlib + pymupdf + pillow，通过 OpenAI 兼容的视觉大模型 HTTP 接口工作。
- **模型注册表**：`models.json`（id/label/base_url/model/key_env/proxy/note），默认 `qwen`（`qwen3-vl-plus`，国内直连）。可选 `gemini` / `openai` / `glm`。Key 在 `.env`：`DASHSCOPE_API_KEY` / `GEMINI_API_KEY` / `OPENAI_API_KEY` / `ZHIPU_API_KEY`。
- **可调参数**：`pages`（如 `1-3,5`）、`dpi`(200–400)、`text_layer`(auto/always/never)、输出类型三选（pdf/html/md）、`mock`（演练模式：不调模型、不花钱）。
- **任务生命周期**（`pdf_translate_jobs.py`）：`_jobs` 内存 dict（最多留 40 个，超出按时间淘汰并删目录）；状态 `queued→running→done|failed`；产物落 `uploads/pdf_translate/<job_id>/out/`。**重启服务即丢失任务列表**（文件仍在磁盘）。
- **成本**：视觉模型 0.01–0.03 元/页；原生电子版 PDF 经文本层路由通常零调用。**调试 UI/流程一律用 mock 模式**，不要花用户的钱。
- **安全**：类型白名单、单文件 ≤80MB、应用 `MAX_CONTENT_LENGTH=100MB`、下载做了 `resolve()` + 前缀校验防路径穿越。
- **已知限制**：无文本层的扫描件用模型 bbox，覆盖式 HTML 可能错位；跨页表格会散；手写体逐页质量不一。

---

## 11. 测试与验证

### 11.1 全页面冒烟（改完必跑）
```python
import sys, werkzeug; sys.path.insert(0,'.'); werkzeug.__version__='3.1.3'
import logging; logging.disable(logging.CRITICAL)
import new_main
c = new_main.app.test_client()
routes = ['/','/qrcode','/date_tag/','/date_tag_view','/bartender_tag/','/queryMaterial',
          '/LSMqueryMaterial','/pdf_translate','/yunHaiPrint','/jinLiPrint','/jiuMaoPrint',
          '/qianJi','/tongtaiying','/fengzhenchang','/fengzhenchang_copy','/zhidongli']
print({p: c.get(p).status_code for p in routes})     # 期望全 200
```

### 11.2 数据层真连（内网必需，冒烟测不出）
```python
import server_connect as sc
df = sc.query_SEord('JHS0282102', 1)          # 真实单号；换 codeName 1..6 各测一遍
print(df.shape, sc.queryMaterial('240').shape, sc.LSMqueryMaterial('胶').shape)
```

### 11.3 PDF 翻译（不花钱）
```python
# 上传 sample + mock=on → 轮询 status → 断言出现 3 个产物 → 逐个下载 200
```

### 11.4 视觉自检（改 UI 时）
```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu \
  --hide-scrollbars --window-size=1440,1000 --virtual-time-budget=5000 \
  --screenshot="D:/tmp/shot.png" "http://127.0.0.1:8080/pdf_translate"
# 深色：URL 加 ?theme=dark
```
截图目录请用临时目录或 `*.shots/`（已 gitignore），**不要提交图片**。

---

## 12. 约定与陷阱（AGENT 必读）

| # | 陷阱 | 说明 / 正确做法 |
|---|---|---|
| 1 | **`manage.bat` 必须 CRLF** | 写成 LF 会导致 cmd 逐行解析错乱（命令被拆成碎片）。用 `p.write_bytes(s.replace('\n','\r\n').encode('utf-8'))` 落地 |
| 2 | **batch 变量延迟展开** | `for /f` 里 `set` 的变量在同一个块内要用 `!VAR!` 而非 `%VAR%` |
| 3 | **`werkzeug.__version__` 缺失** | Flask 2.3.2 的 `test_client()` 会读该属性，Werkzeug 3 已删除 → 测试脚本先 `werkzeug.__version__='3.1.3'`。生产运行不受影响 |
| 4 | **don't `pd.concat([])`** | `process_delivery_data` 已加"全空则提前 return"守卫；新增类似逻辑要照做，否则单号不存在就 500 |
| 5 | **flash 不渲染的坑** | 若新建/复制 base.html，务必保留 `get_flashed_messages()` 区块，否则所有 `flash()` 静默失效 |
| 6 | **旧日志是 GBK** | `logs/app.log.gbk-bak-*` 为历史 GBK，按 UTF-8 读会解码失败；新日志已 UTF-8（RotatingFileHandler encoding） |
| 7 | **`.env` 不入库但要加载** | `.env` 在 `.gitignore`；加载方式是 `new_main._load_env_file()`（零依赖，`setdefault` 语义，不覆盖已有环境变量） |
| 8 | **两份项目副本** | `C:\Users\Administrator\pi-cwd-20260603\system` 是 2026-05 旧快照（停在 `bc387a9`），**不要在那份上改**；以 `D:\VSCODE\PYTHON3\system` 为准 |
| 9 | **密码已进 git 历史** | `server_connect.py` 默认密码 + `DATABASE_CONNECTION.md` 明文。业务决策"内网不改"，但仓库若公开必须轮换 |
| 10 | **不要提交** | `.env`、`uploads/`、`logs/`、`__pycache__/`、`*.shot*`、截图、`*.spec` 产出物。`logs/app.log` 与 `*.pyc` 已 `git rm --cached` |
| 11 | **Git 换行警告** | 提交时大量 `LF will be replaced by CRLF` 属正常（`.gitattributes` 统一） |
| 12 | **PM2/PATH** | 新装 PM2 后当前终端 PATH 未刷新 → 用 `%APPDATA%\npm\pm2.cmd` 或重开终端；`manage.bat` 已做回退 |
| 13 | **端口抢占** | 手工 `python wsgi.py` 与 PM2 同时跑会冲突；换代码后需 `pm2 restart`（Waitress 不热重载） |
| 14 | **推送偶发失败** | GitHub 连接不稳（`Connection was reset`），重试即可；`git -c http.version=HTTP/1.1 push` 更稳 |
| 15 | **别碰打印尺寸** | 打印模板的 mm 数值、`@page`、`visibility:hidden` 补丁是踩坑换来的，改动前先真机验证 |
| 16 | **`write_mysql.py` 危险** | `df.to_sql(..., if_exists='replace')` 会**删表重建**；业务未启用，勿随手调用 |

---

## 13. 常见任务配方

### 13.1 新增一个客户打印模板
1. `server_connect.py`：若字段/聚合不同，新增 `EntryConfig`（新 codeName）与 `_post_code_X`
2. `templates/<name>.html`：`{% extends "base.html" %}`，写 `{% block queryRow %}`（查询条，参考 yunHaiPrint）+ `{% block container %}`（打印纸张）+ 需要时 `{% block head %}` 放 `@page` 与字号
3. `new_main.py` 的 `_PRINT_ROUTES` 追加 `('<route>', codeName, '<name>.html')`
4. `templates/nav.html` 的飞出面板加一条链接
5. 冒烟 + 真机打印验证

### 13.2 新增一个普通功能页
1. `templates/x.html`：`{% extends "base.html" %}`；`{% block topbar %}` 放 `.top-bar`（`h1` + `.sub`），`{% block container %}` 用 `.soft-card` 包裹表单/结果
2. `new_main.py` 加路由，`@handle_errors`
3. `nav.html` 加 `.rail-item`（`<i>` + `<span>` 文字 + `data-match`）
4. 需要入口则同时在 `index.html` 加 `.pastel-card`

### 13.3 改视觉风格
只改 `static/css/theme.css`：优先改变量（配色/圆角/阴影），其次改组件类。**不要**在模板里写内联颜色，也不要新建 CSS 文件分叉。日期标签设计器的独立样式在 `date_tag/index.css` 末尾有一段"接入主系统视觉系统"的桥接层（`var()` 覆盖），改令牌时两边要一致。

### 13.4 加/换依赖
`pyproject.toml` 改 → `uv lock` → `uv sync` → 冒烟 → 同步 `requirements.txt`（生产锁定版）→ 若 Docker 需要，确认 `pip install .` 能装上。

---

## 14. 运维速查

| 动作 | 命令 |
|---|---|
| 启动/停止/重启/状态/日志 | `manage.bat`（选项 1–5），或 `pm2 <cmd> jhs-system` |
| 环境自检/一键补齐 | `manage.bat` 选项 8（Node/npm/PM2/.venv/端口） |
| 保存进程列表（开机自启基础） | `pm2 save`（菜单 7） |
| 注册 Windows 服务（真开机自启） | 管理员执行 `pm2-startup` 后 `pm2 save` |
| 生产端口 | 8080（Waitress）；开发 5000（Flask debug） |
| Linux 生产 | `gunicorn -c gunicorn.conf.py wsgi:application` |
| Docker | `docker compose up -d --build`（需 `.env`；镜像用 msodbcsql18 + `pip install .`） |
| 单文件打包 | `pyinstaller --name wsgi --onefile --windowed --add-data "static;static" --add-data "templates;templates" wsgi.py` |
| 日志 | `logs/app.log`（UTF-8，10MB×5）；`pm2 logs jhs-system` |

---

## 15. 当前状态与已知待办（接手起点）

**已完成（2026-11-16 三批提交）**
1. `46292bf` P0/P1 修复：空单号 500、qrcode XSS、异常信息不外泄、日志 UTF-8、CDN 本地化、依赖统一、Docker 驱动、`.env` 加载、Git 卫生
2. `e08a288` UI 视觉系统重构 `theme.css` + app-shell + 带文字侧栏 + 各页重做 + include→extends
3. `a4af570` / `7a4c2e6` PDF 翻译接入（替换 DeepLX）、`manage.bat` 环境自检与 PM2 自动安装

**待办（按优先级）**
1. `C:\Users\Administrator\pi-cwd-20260603\system` 旧副本确认并清理，避免"改了不生效"
2. 打印模板字体未完全统一：`jiuMaoPrint.html` 仍 `SimSun`，`jinLiPrint.html` 无 `font-family`
3. 无自动化测试与 CI：把 §11 的冒烟/数据层/PDF mock 固化成 `tests/`（DB 用例按内网环境 skip）
4. 死模板可删：`5s.html`、`2024-01-02.html`(5907 行)、`Scheduled_Tasks.html`、`query_seorder.html`、`qianJi222.html`、`testNav.html`；`fengzhenchang_copy` 与 `fengzhenchang` 需定夺保留
5. 性能：数据库连接池（现每次新建）+ 表头/明细合并为一条 JOIN
6. `zhidongli` 的"生产日期"取值规则仍是猜测（`_parse_spec_string` 附近），需业务确认

**不可回退的既有事实**：无鉴权（内网单机）、SQL Server 用 sa、任务状态不持久化、PDF 翻译依赖外部大模型 Key（无 Key 时页面可用但真实翻译会失败，演练模式不受影响）。
