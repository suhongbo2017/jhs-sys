"""测试公共设施：路径注入、Werkzeug 版本补丁、日志静音、样例数据构造。

只依赖标准库 + 项目已有依赖，不引入 pytest。
运行方式：
    .venv/Scripts/python.exe -m unittest discover -s tests -t . -v
"""

import logging
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Flask 2.3.2 的 test_client() 会读 werkzeug.__version__，Werkzeug 3 已删除（AGENTS §12-3）
import werkzeug  # noqa: E402

if not hasattr(werkzeug, '__version__'):
    werkzeug.__version__ = '3.1.3'

# 测试期间不写日志文件、不刷屏
logging.disable(logging.CRITICAL)

os.environ.setdefault('JHS_TEST', '1')

import pandas as pd  # noqa: E402

import new_main  # noqa: E402
import server_connect  # noqa: E402

app = new_main.app


def make_client():
    app.config['TESTING'] = True
    return app.test_client()


# 数值型列（模板里按数值渲染/聚合），其余给字符串
_NUMERIC_COLUMNS = {'数量', '宽', '长', '支', '厚', 'FInterID'}


def sample_entry_df(code_name: int) -> pd.DataFrame:
    """按 ENTRY_CONFIGS 的列定义造一行样例明细，保证模板渲染不炸。"""
    config = server_connect.ENTRY_CONFIGS[code_name]
    row = {c: (1.0 if c in _NUMERIC_COLUMNS else '测试值') for c in config.columns}
    df = pd.DataFrame([row], columns=config.columns)
    df.reset_index(drop=False, inplace=True)
    df.index.name = 'ID'
    return df


def sample_material_df(rows: int = 2) -> pd.DataFrame:
    """物料查询结果样例（列与 _query_material 一致）。"""
    return pd.DataFrame(
        [{
            '物料名称': f'测试物料{i}',
            '规格型号': '10*200*300',
            '物料代码': f'M{i:03d}',
            '短代码': f'S{i:03d}',
            '内码': 1000 + i,
            '单位': 'KG',
        } for i in range(rows)],
        columns=['物料名称', '规格型号', '物料代码', '短代码', '内码', '单位'],
    )


def make_sample_pdf(text: str = 'Test Page') -> bytes:
    """用 pymupdf 生成一页带文本层的 PDF，供 PDF 翻译 mock 流程使用。"""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 100), text, fontsize=18)
    data = doc.tobytes()
    doc.close()
    return data
