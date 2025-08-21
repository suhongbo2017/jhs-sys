# 导入所需的库
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, flash, redirect, url_for, abort
from werkzeug.utils import secure_filename
from flask_bootstrap import Bootstrap # 修改为 flask_bootstrap---
import server_connect
import pandas as pd
import secrets
import os
from functools import wraps
from typing import Optional, Tuple, List, Dict, Any

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

# 创建日志处理器
log_file = os.path.join(log_dir, 'app.log')
handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# 应用配置
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(16))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Bootstrap(app) # 修改为 Bootstrap(app)

    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    return app

app = create_app()

# 错误处理装饰器
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            flash(str(e), "error")
            return render_template('error.html', error=str(e))
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
        datas = pd.concat([server_connect.query_SEord(ds, code_name) for ds in data_list])
        logger.info(f'合并后的内容: {datas.shape[0]} rows')
        return datas, seout_id
    except Exception as e:
        logger.error(f"数据处理错误: {str(e)}")
        raise

# 通用打印请求处理
def handle_print_request(request, code_name: int, template_name: str):
    try:
        data = request.form.get("inputEntry")
        if not data:
            flash('请输入查询内容', 'warning')
            return render_template(template_name)
            
        datas, seout_id = process_delivery_data(data, code_name)
        if datas is None or datas.empty:
            flash('未查询到数据', 'warning')
            return render_template(template_name)
            
        return render_template(template_name, table=datas.iterrows(), data=seout_id)
    except Exception as e:
        logger.error(f"Error in handle_print_request: {str(e)}")
        flash(f"操作出错: {str(e)}", "error")
        return render_template(template_name)

# 路由定义
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/yunHaiPrint', methods=['GET', 'POST'])
@handle_errors
def yunHaiPrint():
    return handle_print_request(request, 1, 'yunHaiPrint.html')

@app.route('/jinLiPrint', methods=['GET', 'POST'])
@handle_errors
def jinLiPrint():
    return handle_print_request(request, 2, 'jinLiPrint.html')

@app.route('/jiuMaoPrint', methods=['GET', 'POST'])
@handle_errors
def jiuMaoPrint():
    return handle_print_request(request, 3, 'jiuMaoPrint.html')

@app.route('/qianJi', methods=['GET', 'POST'])
@handle_errors
def qianJi():
    return handle_print_request(request, 4, 'qianJi.html')

@app.route('/tongtaiying', methods=['GET', 'POST'])
@handle_errors
def tongtaiying():
    return handle_print_request(request, 5, 'tongtaiying.html')

@app.route('/fengzhenchang', methods=['GET', 'POST'])
@handle_errors
def fengzhenchang():
    return handle_print_request(request, 6, 'fengzhenchang.html')

@app.route('/fengzhenchang_copy', methods=['GET', 'POST'])
@handle_errors
def fengzhenchang_copy():    # 修改函数名，避免重复
    return handle_print_request(request, 6, 'fengzhenchang_copy.html')
# 智动力数据处理函数
def process_zhidongli_data(datas: pd.DataFrame) -> pd.DataFrame:
    try:
        newdatas = datas.loc[:, [60, 68, 67, 65, 70, 71, 27]]
        import re
        new71 = newdatas[71].str.split('*')
        newdatas['厚'], newdatas['宽'], newdatas['长'], newdatas['支'] = [re.sub('[URM]', '', x) for x in new71[0]]
        newdatas.drop(71, inplace=True, axis=1)
        
        # 数据映射
        column_mapping = {
            60: '订单号',
            68: '智动力编码',
            67: '品名',
            65: '数量',
            70: '批次号',
            27: '生产日期'
        }
        
        for old_col, new_col in column_mapping.items():
            newdatas[new_col] = newdatas[old_col][0]
            
        newdatas['数量'] = newdatas['数量'].apply(lambda x: round(float(x), 2))
        newdatas['生产日期'] = newdatas['生产日期'].dt.date
        
        # 删除旧列并重排列顺序
        newdatas.drop([60, 68, 67, 65, 70, 27], inplace=True, axis=1)
        return newdatas.loc[:, ['订单号', '智动力编码', '品名', '宽', '长', '厚', '支', '数量', '批次号']]
    except Exception as e:
        logger.error(f"智动力数据处理错误: {str(e)}")
        raise

@app.route('/zhidongli', methods=['GET', 'POST'])
@handle_errors
def zhidongli():
    try:
        data = request.form.get("inputEntry")
        if not data:
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
        logger.error(f"Error in zhidongli route: {str(e)}")
        flash(f"操作出错: {str(e)}", "error")
        return render_template('zhidongli.html')

# 物料查询处理函数
def process_material_query(q_data: str, query_func) -> Tuple[Optional[pd.DataFrame], str]:
    if '/' in q_data:
        conditions = q_data.split('/')
        if len(conditions) != 2:
            raise ValueError("查询格式错误：请使用'/'分隔两个查询条件")
            
        datas = query_func(conditions[0])
        result = datas.loc[
            (datas['物料名称'].str.contains(conditions[1])) |
            (datas['规格型号'].str.contains(conditions[1]))
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
            flash('未查询到数据，请检查输入', 'warning')
            return render_template('queryMaterial.html')
            
        logger.info(f"{query_type}成功: {result.shape[0]} 条记录")
        return render_template('queryMaterial.html', datas=result.iterrows())
    except ValueError as ve:
        logger.warning(f"查询格式错误: {str(ve)}")
        flash(str(ve), 'warning')
        return render_template('queryMaterial.html')
    except Exception as e:
        logger.error(f"Error in queryMaterial: {str(e)}")
        flash(f"查询出错: {str(e)}", "error")
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
            flash('未查询到数据，请检查输入', 'warning')
            return render_template('LSMqueryMaterial.html')
            
        logger.info(f"LSM{query_type}成功: {result.shape[0]} 条记录")
        return render_template('LSMqueryMaterial.html', datas=result.iterrows())
    except ValueError as ve:
        logger.warning(f"LSM查询格式错误: {str(ve)}")
        flash(str(ve), 'warning')
        return render_template('LSMqueryMaterial.html')
    except Exception as e:
        logger.error(f"Error in LSMqueryMaterial: {str(e)}")
        flash(f"查询出错: {str(e)}", "error")
        return render_template('LSMqueryMaterial.html')

@app.route('/translate', methods=['GET', 'POST'])
@handle_errors
def translate():
    try:
        strs = request.form.get('translate')
        lang = request.form.get('lang')
        
        if not strs:
            logger.warning("未提供翻译文本")
            flash('请输入要翻译的内容', 'warning')
            return render_template('translate.html')
            
        logger.info(f"翻译请求 - 语言: {lang}, 文本: {strs}")
        
        from PyDeepLX import PyDeepLX as dx
        translator = dx()
        result = translator.translate(strs, source_lang="auto", target_lang=lang)
        
        logger.info(f"翻译完成: {result}")
        return render_template('translate.html', result=result)
    except Exception as e:
        logger.error(f"翻译错误: {str(e)}")
        flash(f"翻译出错: {str(e)}", "error")
        return render_template('translate.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
