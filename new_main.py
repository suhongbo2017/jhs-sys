# 导入所需的库
import logging
from logging.handlers import RotatingFileHandler
from flask import (Flask, render_template, request, flash, send_from_directory,
                   redirect, url_for, jsonify)
from flask_bootstrap import Bootstrap4
import server_connect
import pdf_translate_jobs
import pandas as pd
import os
import re
from functools import wraps
import threading
from typing import Optional, Tuple, List, Any

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)


def _load_env_file(path: str = None) -> None:
    """零依赖加载 .env（不覆盖已存在的环境变量）。替代 python-dotenv。"""
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if not os.path.isfile(path):
        return
    with open(path, encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, _, value = line.partition('=')
            key, value = key.strip(), value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value


_load_env_file()

# 创建日志处理器
log_file = os.path.join(log_dir, 'app.log')
handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5, encoding='utf-8')
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# ===== 应用工厂 =====
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(16).hex())
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
    app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # PDF 翻译需要更大上传额度

    Bootstrap4(app)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('error.html', error='页面未找到 (404)'), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"服务器内部错误: {e}", exc_info=True)
        return render_template('error.html', error='服务器内部错误 (500)'), 500

    return app

app = create_app()

# 错误处理装饰器
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
            flash('操作出错，详情请查看服务日志', "error")
            return render_template('error.html', error='操作出错，详情请查看服务日志')
    return decorated_function

# 文件类型验证
def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# 数据处理函数
def process_delivery_data(data: str, code_name: int) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    if not data:
        return None, None
    
    data = data.upper()
    seout_id = data
    data_list = data.split('/')
    logger.info(f"格式化输入单号：{data_list}")
    
    try:
        # 过滤掉空的 DataFrame（全部未命中时避免 concat([]) 抛 ValueError）
        results = [server_connect.query_SEord(ds, code_name) for ds in data_list]
        non_empty = [df for df in results if not df.empty]
        if not non_empty:
            return None, None

        datas = pd.concat(non_empty)
        
        if datas.empty:
            return None, None

        logger.info(f'合并后的内容: {datas.shape[0]} rows')
        return datas, seout_id
    except Exception as e:
        logger.error(f"数据处理错误: {str(e)}", exc_info=True)
        raise

# 通用打印请求处理
def handle_print_request(request, code_name: int, template_name: str):
    try:
        data = request.form.get("inputEntry")
        if not data:
            # 仅 POST 时提示，GET 直接访问保持页面干净
            if request.method == 'POST':
                flash('请输入查询内容', 'warning')
            return render_template(template_name)
            
        datas, seout_id = process_delivery_data(data, code_name)
        if datas is None or datas.empty:
            flash('未查询到数据', 'warning')
            return render_template(template_name)
            
        # 将 DataFrame 转换为字典列表
        return render_template(template_name, table=datas.to_dict(orient='records'), data=seout_id)
    except Exception as e:
        logger.error(f"Error in handle_print_request: {str(e)}", exc_info=True)
        flash('操作出错，详情请查看服务日志', "error")
        return render_template(template_name)

# ===== 路由定义 =====
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/qrcode')
def show_qrcode():
    return render_template('qrcode.html')

@app.route('/date_tag/')
def date_tag():
    return send_from_directory('date_tag', 'index.html')

@app.route('/date_tag_view')
def date_tag_view():
    return render_template('date_tag_view.html')

@app.route('/date_tag/<path:path>')
def date_tag_static(path):
    return send_from_directory('date_tag', path)

@app.route('/bartender_tag/')
def bartender_tag():
    return render_template('tag_code2026.html')

# 打印路由：动态注册（7 个路由合并为 1 个列表）
_PRINT_ROUTES = [
    ('yunHaiPrint', 1, 'yunHaiPrint.html'),
    ('jinLiPrint', 2, 'jinLiPrint.html'),
    ('jiuMaoPrint', 3, 'jiuMaoPrint.html'),
    ('qianJi', 4, 'qianJi.html'),
    ('tongtaiying', 5, 'tongtaiying.html'),
    ('fengzhenchang', 6, 'fengzhenchang.html'),
    ('fengzhenchang_copy', 6, 'fengzhenchang_copy.html'),
]

for _route_name, _code, _template in _PRINT_ROUTES:
    def _make_handler(cn=_code, tmpl=_template, name=_route_name):
        @handle_errors
        def handler():
            return handle_print_request(request, cn, tmpl)
        handler.__name__ = name
        return handler
    app.add_url_rule(f'/{_route_name}', _route_name, _make_handler(), methods=['GET', 'POST'])
# 智动力数据处理函数
def process_zhidongli_data(datas: pd.DataFrame) -> pd.DataFrame:
    try:
        # 假设 codeName=2 返回的列名为：['物料名称', '整支规格', '料号', '批号', '订单号', '数量', '备注', '批次号']
        # 根据实际需求选择和重命名列
        newdatas = datas[['订单号', '批次号', '物料名称', '数量', '整支规格', '备注']].copy()
        
        # 解析 '整支规格' 列，并添加健壮性检查
        newdatas[['厚', '宽', '长', '支']] = pd.DataFrame([
            _parse_spec_string(spec) for spec in newdatas['整支规格']
        ], index=newdatas.index)
        
        newdatas.drop('整支规格', axis=1, inplace=True) # 删除原始整支规格列
        
        # 数据映射和重命名
        column_mapping = {
            '订单号': '订单号',
            '批次号': '智动力编码', # 假设批次号对应智动力编码
            '物料名称': '品名',
            '数量': '数量',
            '备注': '生产日期' # 假设备注对应生产日期，需要进一步确认逻辑
        }
        newdatas.rename(columns=column_mapping, inplace=True)
        
        newdatas['数量'] = newdatas['数量'].apply(lambda x: round(float(x), 2))
        # 生产日期可能需要更复杂的解析，这里假设备注中包含日期信息
        # newdatas['生产日期'] = pd.to_datetime(newdatas['生产日期'], errors='coerce').dt.date
        
        # 重新排列顺序
        return newdatas.loc[:, ['订单号', '智动力编码', '品名', '宽', '长', '厚', '支', '数量', '生产日期']]
    except Exception as e:
        logger.error(f"智动力数据处理错误: {str(e)}", exc_info=True)
        raise

# 辅助函数：解析规格字符串
def _parse_spec_string(spec_string: str) -> List[Any]:
    # 示例解析逻辑，需要根据实际的规格字符串格式进行调整
    # 假设格式为 "厚*宽*长*支" 或类似
    parts = re.findall(r'(\d+\.?\d*)[URM]*', str(spec_string))
    # 确保返回固定数量的元素，不足时填充 None 或默认值
    parsed_values = [float(p) if p else None for p in parts]
    return (parsed_values + [None] * 4)[:4] # 确保返回4个元素

@app.route('/zhidongli', methods=['GET', 'POST'])
@handle_errors
def zhidongli():
    try:
        data = request.form.get("inputEntry")
        if not data:
            if request.method == 'POST':
                flash('请输入查询内容', 'warning')
            return render_template('zhidongli.html')
            
        datas, seout_id = process_delivery_data(data, 2)
        if datas is None or datas.empty:
            flash('未查询到数据', 'warning')
            return render_template('zhidongli.html')
            
        processed_data = process_zhidongli_data(datas)
        logger.info(f'处理后的数据: {processed_data.shape[0]} rows')
        
        return render_template('zhidongli.html',
                             tables=processed_data.to_dict(orient='records'),
                             data=seout_id,
                             names=processed_data.columns)
    except Exception as e:
        logger.error(f"Error in zhidongli route: {str(e)}", exc_info=True)
        flash('操作出错，详情请查看服务日志', "error")
        return render_template('zhidongli.html')

# 物料查询处理函数
def process_material_query(q_data: str, query_func) -> Tuple[Optional[pd.DataFrame], str]:
    if '/' in q_data:
        conditions = q_data.split('/')
        if len(conditions) != 2:
            raise ValueError("查询格式错误：请使用'/'分隔两个查询条件")
            
        datas = query_func(conditions[0])
        if datas.empty:
            return pd.DataFrame(), "多条件查询" # 返回空 DataFrame
        
        result = datas.loc[
            (datas['物料名称'].str.contains(conditions[1], na=False)) |
            (datas['规格型号'].str.contains(conditions[1], na=False))
        ]
        return result, "多条件查询"
    else:
        return query_func(q_data), "单条件查询"

@app.route('/queryMaterial', methods=['GET', 'POST'])
@handle_errors
def queryMaterial():
    try:
        q_data = request.form.get('material')
        if not q_data:
            return render_template('queryMaterial.html')
            
        logger.info(f"查询输入: {q_data}")
        result, query_type = process_material_query(q_data, server_connect.queryMaterial)
        
        if result.empty:
            logger.warning(f"未查询到数据: {q_data}")
            # 提示显示在下方查询结果区域内（不再用顶部 flash）
            return render_template('queryMaterial.html',
                                   message='未查询到数据，请检查输入')
            
        logger.info(f"{query_type}成功: {result.shape[0]} 条记录")
        return render_template('queryMaterial.html', datas=result.iterrows())
    except ValueError as ve:
        logger.warning(f"查询格式错误: {str(ve)}")
        return render_template('queryMaterial.html', message=str(ve))
    except Exception as e:
        logger.error(f"Error in queryMaterial: {str(e)}", exc_info=True)
        flash('查询出错，详情请查看服务日志', "error")
        return render_template('queryMaterial.html')

@app.route('/LSMqueryMaterial', methods=['GET', 'POST'])
@handle_errors
def LSMqueryMaterial():
    try:
        q_data = request.form.get('material')
        if not q_data:
            return render_template('LSMqueryMaterial.html')
            
        logger.info(f"LSM查询输入: {q_data}")
        result, query_type = process_material_query(q_data, server_connect.LSMqueryMaterial)
        
        if result.empty:
            logger.warning(f"LSM未查询到数据: {q_data}")
            # 提示显示在下方查询结果区域内（不再用顶部 flash）
            return render_template('LSMqueryMaterial.html',
                                   message='未查询到数据，请检查输入')
            
        logger.info(f"LSM{query_type}成功: {result.shape[0]} 条记录")
        return render_template('LSMqueryMaterial.html', datas=result.iterrows())
    except ValueError as ve:
        logger.warning(f"LSM查询格式错误: {str(ve)}")
        return render_template('LSMqueryMaterial.html', message=str(ve))
    except Exception as e:
        logger.error(f"Error in LSMqueryMaterial: {str(e)}", exc_info=True)
        flash('查询出错，详情请查看服务日志', "error")
        return render_template('LSMqueryMaterial.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

# ============================================================
# PDF / 扫描件 翻译（复用 vendored pdftranslate 流水线）
# ============================================================
@app.route('/pdf_translate', methods=['GET', 'POST'])
@handle_errors
def pdf_translate():
    if request.method == 'POST':
        uploads = request.files.getlist('files')
        files: List[Tuple[str, bytes]] = []
        for f in uploads:
            if not f or not f.filename:
                continue
            files.append((f.filename, f.read()))

        model_id = request.form.get('model') or pdf_translate_jobs.default_model()
        pages = request.form.get('pages', '')
        try:
            dpi = int(request.form.get('dpi') or 250)
        except ValueError:
            dpi = 250
        want_pdf = request.form.get('want_pdf') == 'on'
        want_html = request.form.get('want_html') == 'on'
        want_md = request.form.get('want_md') == 'on'
        if not (want_pdf or want_html or want_md):
            want_pdf = want_html = want_md = True
        mock = request.form.get('mock') == 'on'

        job_id, err = pdf_translate_jobs.create_job(
            files=files, model_id=model_id, pages=pages, dpi=dpi,
            want_pdf=want_pdf, want_html=want_html, want_md=want_md,
            text_layer=request.form.get('text_layer', 'auto'), mock=mock,
        )
        if err:
            flash(err, 'warning')
            return render_template('pdf_translate.html',
                                   models=pdf_translate_jobs.available_models(),
                                   default_model=pdf_translate_jobs.default_model(),
                                   jobs=pdf_translate_jobs.list_jobs())
        logger.info(f"PDF 翻译任务已创建: {job_id}")
        return redirect(url_for('pdf_translate', job=job_id))

    return render_template('pdf_translate.html',
                           models=pdf_translate_jobs.available_models(),
                           default_model=pdf_translate_jobs.default_model(),
                           jobs=pdf_translate_jobs.list_jobs(),
                           job=request.args.get('job', ''))


@app.route('/pdf_translate/status/<job_id>')
def pdf_translate_status(job_id: str):
    job = pdf_translate_jobs.get_job(job_id)
    if not job:
        return jsonify({'error': '任务不存在或已过期'}), 404
    return jsonify(job)


@app.route('/pdf_translate/download/<job_id>/<path:name>')
def pdf_translate_download(job_id: str, name: str):
    workdir = pdf_translate_jobs.job_dir(job_id)
    if not workdir:
        flash('任务不存在或已过期', 'warning')
        return redirect(url_for('pdf_translate'))
    out_dir = (workdir / 'out').resolve()
    target = (out_dir / name).resolve()
    if not str(target).startswith(str(out_dir)) or not target.is_file():
        flash('文件不存在', 'warning')
        return redirect(url_for('pdf_translate'))
    return send_from_directory(out_dir, name, as_attachment=True)
