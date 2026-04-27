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
import re # 导入 re 模块
from functools import wraps
from typing import Optional, Tuple, List, Dict, Any
from PyDeepLX import PyDeepLX as dx # 将 PyDeepLX 导入移到顶部

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
            logger.error(f"Error in {f.__name__}: {str(e)}", exc_info=True)
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
        # 过滤掉空的 DataFrame
        results = [server_connect.query_SEord(ds, code_name) for ds in data_list]
        datas = pd.concat([df for df in results if not df.empty])
        
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
            flash('请输入查询内容', 'warning')
            return render_template(template_name)
            
        datas, seout_id = process_delivery_data(data, code_name)
        if datas is None or datas.empty:
            flash('未查询到数据', 'warning')
            return render_template(template_name)
            
        # 使用 iterrows() 以匹配模板中的 {% for d,i in table %}
        return render_template(template_name, table=datas.iterrows(), data=seout_id)
    except Exception as e:
        logger.error(f"Error in handle_print_request: {str(e)}", exc_info=True)
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
            flash('请输入查询内容', 'warning')
            return render_template('zhidongli.html')
            
        datas, seout_id = process_delivery_data(data, 2)
        if datas is None or datas.empty:
            flash('未查询到数据', 'warning')
            return render_template('zhidongli.html')
            
        processed_data = process_zhidongli_data(datas)
        logger.info(f'处理后的数据: {processed_data.shape[0]} rows')
        
        return render_template('zhidongli.html',
                             tables=processed_data.iterrows(),
                             data=seout_id,
                             names=processed_data.columns)
    except Exception as e:
        logger.error(f"Error in zhidongli route: {str(e)}", exc_info=True)
        flash(f"操作出错: {str(e)}", "error")
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
            flash('未查询到数据，请检查输入', 'warning')
            return render_template('queryMaterial.html')
            
        logger.info(f"{query_type}成功: {result.shape[0]} 条记录")
        return render_template('queryMaterial.html', datas=result.iterrows())
    except ValueError as ve:
        logger.warning(f"查询格式错误: {str(ve)}")
        flash(str(ve), 'warning')
        return render_template('queryMaterial.html')
    except Exception as e:
        logger.error(f"Error in queryMaterial: {str(e)}", exc_info=True)
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
        logger.error(f"Error in LSMqueryMaterial: {str(e)}", exc_info=True)
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
        
        translator = dx()
        result = translator.translate(strs, source_lang="auto", target_lang=lang)
        
        logger.info(f"翻译完成: {result}")
        return render_template('translate.html', result=result)
    except Exception as e:
        logger.error(f"翻译错误: {str(e)}", exc_info=True)
        flash(f"翻译出错: {str(e)}", "error")
        return render_template('translate.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
