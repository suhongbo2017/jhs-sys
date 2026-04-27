'''本函数是对金蝶数据库中的送货单表头和表体进行查询，得到分列的数据进行汇总后返回。'''

import pyodbc
import pandas as pd
import os
import logging
from logging.handlers import RotatingFileHandler # 确保导入 RotatingFileHandler

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 从环境变量获取数据库配置
server = os.getenv('DB_SERVER', '192.168.0.234')
database = os.getenv('DB_DATABASE', 'AIS20191210135722')
username = os.getenv('DB_USERNAME', 'sa')
password = os.getenv('DB_PASSWORD', 'Jhs16888')
DSN = 'seord'

# 定义数据库 schema 常量
DB_SCHEMA_2019 = f"{database}.dbo"
DB_SCHEMA_2023 = "AIS20230525154804.dbo" # 假设这个数据库是固定的，如果也需要动态，则从环境变量获取

def get_connection():
    """获取数据库连接"""
    try:
        connection_string = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};trustServerCertificate=yes;'
        return pyodbc.connect(connection_string)
    except Exception as e:
        logger.error(f"数据库连接错误: {e}", exc_info=True)
        raise

# 辅助函数：处理 codeName = 1 的逻辑
def _handle_code_1(cursor, finter_id):
    sql1 = f"SELECT FEntrySelfS0257, FEntrySelfS0240,FEntrySelfS0258,FEntrySelfS0248,FEntrySelfS0239,FEntrySelfS0244, FEntrySelfS0263 FROM {DB_SCHEMA_2019}.SEOutStockEntry WHERE FInterID = ?"
    cursor.execute(sql1, finter_id)
    rows1 = cursor.fetchall()
    data1 = [[j for j in i] for i in rows1]
    columns = ['物料名称', '整支规格', '料号', '批号', '订单号', '数量', '备注']
    dfs = pd.DataFrame(data1, columns=columns)
    dfs['数量'] = dfs['数量'].apply(float).round(2)
    dfs['备注'] = dfs['备注'].apply(lambda x: ('*'.join(str(x).split('*')[-3::2]).replace('M', '') + ' '))
    dfs = dfs.groupby('物料名称').agg({'整支规格': 'first', '料号': 'first', '批号': 'first', '订单号': 'first', '数量': 'sum', '备注': 'sum'})
    dfs['数量'] = dfs['数量'].apply(float).round(2)
    dfs.reset_index(drop=False, inplace=True)
    dfs.index.name = 'ID'
    return dfs

# 辅助函数：处理 codeName = 2 的逻辑
def _handle_code_2(cursor, finter_id):
    sql2 = f"SELECT FEntrySelfS0257, FEntrySelfS0240, FEntrySelfS0258, FEntrySelfS0248, FEntrySelfS0239, FEntrySelfS0244, FEntrySelfS0263, FNote FROM {DB_SCHEMA_2019}.SEOutStockEntry WHERE FINTERID = ?"
    cursor.execute(sql2, finter_id)
    rows1 = cursor.fetchall()
    # 为 codeName=2 定义明确的列名
    columns = ['物料名称', '整支规格', '料号', '批号', '订单号', '数量', '备注', '批次号']
    dfs = pd.DataFrame(rows1, columns=columns)
    dfs.reset_index(drop=False, inplace=True)
    dfs.index.name = 'ID'
    return dfs

# 辅助函数：处理 codeName = 3 的逻辑
def _handle_code_3(cursor, finter_id):
    sql3 = f"SELECT FEntrySelfS0239, FEntrySelfS0258,FEntrySelfS0257,FEntrySelfS0241,FEntrySelfS0242,FEntrySelfS0243, FEntrySelfS0244, FEntrySelfS0248 FROM {DB_SCHEMA_2019}.SEOutStockEntry WHERE FInterID = ?"
    cursor.execute(sql3, finter_id)
    rows1 = cursor.fetchall()
    data1 = [[j for j in i] for i in rows1]
    columns = ['客户订单号', '客户品号', '客户品名', '宽', '长', '支', '数量', '批号']
    dfs = pd.DataFrame(data1, columns=columns)
    dfs['宽'] = dfs['宽'].apply(float).round(2)
    dfs['长'] = dfs['长'].apply(float).round(2)
    dfs['支'] = dfs['支'].apply(int)
    dfs['数量'] = dfs['数量'].apply(float).round(2)
    dfs.reset_index(drop=False, inplace=True)
    dfs.index.name = 'ID'
    return dfs

# 辅助函数：处理 codeName = 4 的逻辑
def _handle_code_4(cursor, finter_id):
    sql2 = f"SELECT FEntrySelfS0257, FEntrySelfS0240,FNote,FEntrySelfS0258,FEntrySelfS0248,FEntrySelfS0239,FEntrySelfS0244, FEntrySelfS0263 FROM {DB_SCHEMA_2019}.SEOutStockEntry WHERE FInterID = ?"
    cursor.execute(sql2, finter_id)
    rows1 = cursor.fetchall()
    data1 = [[j for j in i] for i in rows1]
    columns = ['物料名称', '备注', '批次号', '料号', '批号', '订单号', '数量', '整支规格']
    dfs = pd.DataFrame(data1, columns=columns)
    dfs['数量'] = dfs['数量'].apply(float).round(2)
    dfs['整支规格'] = dfs['整支规格'].apply(lambda x: '*'.join(str(x).split("*")[1:]) + '+ ')
    dfs = dfs.groupby('物料名称').agg({'整支规格': 'sum', '料号': 'first', '批次号': 'first', '订单号': 'first', '数量': 'sum', '备注': 'first'})
    dfs['数量'] = dfs['数量'].apply(float).round(2)
    dfs.reset_index(drop=False, inplace=True)
    dfs.index.name = 'ID'
    return dfs

# 辅助函数：处理 codeName = 5 或 6 的逻辑
def _handle_code_5_6(cursor, finter_id):
    sql3 = f"SELECT FEntrySelfS0239, FEntrySelfS0258,FEntrySelfS0257,FEntrySelfS0241,FNote,FEntrySelfS0240,FEntrySelfS0243,FEntrySelfS0242, FEntrySelfS0244, FEntrySelfS0248 FROM {DB_SCHEMA_2019}.SEOutStockEntry WHERE FInterID = ?"
    cursor.execute(sql3, finter_id)
    rows1 = cursor.fetchall()
    data1 = [[j for j in i] for i in rows1]
    columns = ['采购订单', 'TTY新料号', '产品名称', '宽', '型号', '规格', '支', '长', '数量', '批号']
    dfs = pd.DataFrame(data1, columns=columns)
    dfs['宽'] = dfs['宽'].apply(int).round(0)
    dfs['长'] = dfs['长'].apply(int).round(0)
    dfs['支'] = dfs['支'].apply(int).round(0)
    dfs['数量'] = dfs['数量'].apply(float).round(2)
    dfs.reset_index(drop=False, inplace=True)
    dfs.index.name = 'ID'
    return dfs

# codeName 映射字典
CODE_HANDLERS = {
    1: _handle_code_1,
    2: _handle_code_2,
    3: _handle_code_3,
    4: _handle_code_4,
    5: _handle_code_5_6,
    6: _handle_code_5_6,
}

# 查询送货单表头数据
def query_SEord(params, codeName):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # 查询语句
            sql = f"SELECT FInterID, FBillNo, FTranType, FSalType, FCustID FROM {DB_SCHEMA_2019}.SEOutStock WHERE FBILLNO = ?"
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            if not rows:
                logger.warning(f"未查询到送货单表头数据，单号: {params}")
                return pd.DataFrame()

            finter_id = rows[0][0] # 获取 FInterID

            handler = CODE_HANDLERS.get(codeName)
            if handler:
                return handler(cursor, finter_id)
            else:
                logger.warning(f"未知的 codeName: {codeName}")
                return pd.DataFrame()
    except Exception as e:
        logger.error(f'query_SEord 出现错误: {e}', exc_info=True)
        return pd.DataFrame()

def queryMaterial(params):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # 查询语句
            like_param = f"%{params}%"
            sql = f"""
            SELECT t1.FName, t1.FModel, t1.FNumber, t1.FShortNumber, t1.FItemID, t3.FName as FUnitName
            FROM {DB_SCHEMA_2019}.t_ICItemCore t1
            JOIN {DB_SCHEMA_2019}.t_ICItemBase t2 ON t1.FItemID = t2.FItemID
            JOIN {DB_SCHEMA_2019}.t_MeasureUnit t3 ON t2.FUnitID = t3.FMeasureUnitID
            WHERE t1.FNAME LIKE ? or t1.FModel LIKE ? or t1.FNumber LIKE ?;
            """
            cursor.execute(sql, like_param, like_param, like_param)

            rows1 = cursor.fetchall()
            if not rows1:
                logger.warning(f'queryMaterial 查询结果为空: {params}')
                return pd.DataFrame()
            
            data1 = [[j for j in i] for i in rows1]
            columns = ['物料名称', '规格型号', '物料代码', '短代码', '内码', '单位']
            dfs = pd.DataFrame(data1, columns=columns)
            logger.info(f'queryMaterial 查询成功，返回 {dfs.shape[0]} 条记录')
            return dfs
    except Exception as e:
        logger.error(f'queryMaterial 出现错误: {e}', exc_info=True)
        return pd.DataFrame()
    
def LSMqueryMaterial(params):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # 查询语句
            like_param = f"%{params}%"
            sql = f"""
            SELECT t1.FName, t1.FModel, t1.FNumber, t1.FShortNumber, t1.FItemID, t3.FName as FUnitName
            FROM {DB_SCHEMA_2023}.t_ICItemCore t1
            JOIN {DB_SCHEMA_2023}.t_ICItemBase t2 ON t1.FItemID = t2.FItemID
            JOIN {DB_SCHEMA_2023}.t_MeasureUnit t3 ON t2.FUnitID = t3.FMeasureUnitID
            WHERE t1.FNAME LIKE ? or t1.FModel LIKE ? or t1.FNumber LIKE ?;
            """
            cursor.execute(sql, like_param, like_param, like_param)

            rows1 = cursor.fetchall()
            if not rows1:
                logger.warning(f'LSMqueryMaterial 查询结果为空: {params}')
                return pd.DataFrame()
            
            data1 = [[j for j in i] for i in rows1]
            columns = ['物料名称', '规格型号', '物料代码', '短代码', '内码', '单位']
            dfs = pd.DataFrame(data1, columns=columns)
            logger.info(f'LSMqueryMaterial 查询成功，返回 {dfs.shape[0]} 条记录')
            return dfs
    except Exception as e:
        logger.error(f'LSMqueryMaterial 出现错误: {e}', exc_info=True)
        return pd.DataFrame()

if __name__ == "__main__":
    # 示例用法
    # 配置日志处理器，仅在直接运行时添加，避免在作为模块导入时重复添加
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'server_connect.log')
    handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    # 测试 query_SEord
    df = query_SEord('JHS0172378', 5)
    if not df.empty:
        print("query_SEord 结果:")
        print(df)
    else:
        print("query_SEord 未返回数据或发生错误。")

    # 测试 queryMaterial
    df_material = queryMaterial('物料')
    if not df_material.empty:
        print("\nqueryMaterial 结果:")
        print(df_material.head())
    else:
        print("queryMaterial 未返回数据或发生错误。")

    # 测试 LSMqueryMaterial
    df_lsm_material = LSMqueryMaterial('物料')
    if not df_lsm_material.empty:
        print("\nLSMqueryMaterial 结果:")
        print(df_lsm_material.head())
    else:
        print("LSMqueryMaterial 未返回数据或发生错误。")
