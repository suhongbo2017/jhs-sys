# tests/ — 自动化测试套件

标准库 `unittest`，**不新增依赖**，直接用项目 venv 跑。

```bash
cd /d/VSCODE/PYTHON3/system

# 全量（约 4 秒；真连数据库的用例默认跳过）
.venv/Scripts/python.exe -m unittest discover -s tests -t . -v

# 单独跑某一组
.venv/Scripts/python.exe -m unittest tests.test_print -v

# 真连内网数据库（可选）
set RUN_LIVE_DB=1 && set LIVE_BILL_NO=JHS0282102 && .venv/Scripts/python.exe -m unittest tests.test_live_db -v
```

## 用例分布

| 文件 | 覆盖 | 是否需要 DB |
|---|---|---|
| `test_routes.py` | 16 个 GET 路由 200、404 自定义页、GET 不弹提示、无外网 CDN | 否 |
| `test_print.py` | 7 个打印路由 + 智动力：空输入/未命中/命中/多单号/异常兜底；物料查询命中、未命中、格式错误、异常不外泄 | 否（`query_SEord` 打桩） |
| `test_units.py` | `process_delivery_data`（空/全空/部分命中/多单号/空白容错）、`_parse_spec_string`、`process_zhidongli_data`、`process_material_query`（多条件/正则字面量/去空格）、`allowed_file`、`_load_env_file` | 否 |
| `test_pdf_translate.py` | 上传校验、任务状态 404、下载路径穿越拦截、mock 全流程（生成 1 页 PDF → 轮询 → 下载产物） | 否，不调模型 |
| `test_live_db.py` | 真实 `query_SEord` 各 codeName、物料查询 | **是**，默认跳过 |

## 约定

- `tests/support.py` 负责 sys.path 注入、`werkzeug.__version__` 补丁（AGENTS §12-3）、日志静音、样例数据构造。
- **不要**在测试里连外网或真实调用视觉模型；PDF 流程一律 `mock=True`。
- PDF mock 用例会在 `uploads/pdf_translate/` 下留下任务目录，属 gitignore 范围。
- 新增路由/模板时，在 `test_routes.ROUTES` 和（打印类）`test_print.PRINT_ROUTES` 里补一行。
