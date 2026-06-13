'''金蝶数据库查询模块：送货单表头/表体查询、物料查询'''

import pyodbc
import pandas as pd
import os
import logging
from logging.handlers import RotatingFileHandler
from dataclasses import dataclass
from typing import Optional, Callable

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ===== 数据库配置（内网使用，密码直接写在代码中）=====
server = os.getenv('DB_SERVER', '192.168.0.234')
database = os.getenv('DB_DATABASE', 'AIS20191210135722')
username = os.getenv('DB_USERNAME', 'sa')
password = 'Jhs16888'

DB_SCHEMA_2019 = f"{database}.dbo"
DB_SCHEMA_2023 = os.getenv('DB_SCHEMA_2023', 'AIS20230525154804.dbo')

COLUMNS_SEOUTSTOCK = [
    'FInterID', 'FBillNo', 'FTranType', 'FSalType', 'FCustID'
]


# ===== 数据库连接 =====
def get_connection():
    """获取数据库连接（连接不缓存，由 with 块管理生命周期）"""
    conn_str = (
        f'DRIVER={{SQL Server}};'
        f'SERVER={server};DATABASE={database};'
        f'UID={username};PWD={password};'
    )
    return pyodbc.connect(conn_str)


# ===== 查询配置（数据驱动替代 6 个重复函数）=====
@dataclass
class EntryConfig:
    """送货单明细查询配置"""
    columns: list[str]
    sql_fields: str
    post_process: Optional[Callable] = None


def _post_code_1(df: pd.DataFrame) -> pd.DataFrame:
    """codeName=1 后处理：备注截取 + groupby 聚合"""
    df['数量'] = df['数量'].astype(float).round(2)
    df['备注'] = df['备注'].apply(
        lambda x: ('*'.join(str(x).split('*')[-3::2]).replace('M', '') + ' ')
    )
    df = df.groupby('物料名称', as_index=False).agg({
        '整支规格': 'first', '料号': 'first', '批号': 'first',
        '订单号': 'first', '数量': 'sum', '备注': 'sum'
    })
    df['数量'] = df['数量'].round(2)
    return df


def _post_code_4(df: pd.DataFrame) -> pd.DataFrame:
    """codeName=4 后处理：规格拼接 + groupby 聚合"""
    df['数量'] = df['数量'].astype(float).round(2)
    df['整支规格'] = df['整支规格'].apply(
        lambda x: '*'.join(str(x).split("*")[1:]) + '+ '
    )
    df = df.groupby('物料名称', as_index=False).agg({
        '整支规格': 'sum', '料号': 'first', '批次号': 'first',
        '订单号': 'first', '数量': 'sum', '备注': 'first'
    })
    df['数量'] = df['数量'].round(2)
    return df


def _post_code_3(df: pd.DataFrame) -> pd.DataFrame:
    """codeName=3 后处理：数值类型转换"""
    df['宽'] = df['宽'].astype(float).round(2)
    df['长'] = df['长'].astype(float).round(2)
    df['支'] = df['支'].astype(int)
    df['数量'] = df['数量'].astype(float).round(2)
    return df


def _post_code_5_6(df: pd.DataFrame) -> pd.DataFrame:
    """codeName=5/6 后处理：数值类型转换"""
    df['宽'] = df['宽'].astype(int)
    df['长'] = df['长'].astype(int)
    df['支'] = df['支'].astype(int)
    df['数量'] = df['数量'].astype(float).round(2)
    return df


ENTRY_CONFIGS: dict[int, EntryConfig] = {
    1: EntryConfig(
        columns=['物料名称', '整支规格', '料号', '批号', '订单号', '数量', '备注'],
        sql_fields='FEntrySelfS0257, FEntrySelfS0240, FEntrySelfS0258, '
                   'FEntrySelfS0248, FEntrySelfS0239, FEntrySelfS0244, FEntrySelfS0263',
        post_process=_post_code_1,
    ),
    2: EntryConfig(
        columns=['物料名称', '整支规格', '料号', '批号', '订单号', '数量', '备注', '批次号'],
        sql_fields='FEntrySelfS0257, FEntrySelfS0240, FEntrySelfS0258, '
                   'FEntrySelfS0248, FEntrySelfS0239, FEntrySelfS0244, FEntrySelfS0263, FNote',
    ),
    3: EntryConfig(
        columns=['客户订单号', '客户品号', '客户品名', '宽', '长', '支', '数量', '批号'],
        sql_fields='FEntrySelfS0239, FEntrySelfS0258, FEntrySelfS0257, '
                   'FEntrySelfS0241, FEntrySelfS0242, FEntrySelfS0243, FEntrySelfS0244, FEntrySelfS0248',
        post_process=_post_code_3,
    ),
    4: EntryConfig(
        columns=['物料名称', '备注', '批次号', '料号', '批号', '订单号', '数量', '整支规格'],
        sql_fields='FEntrySelfS0257, FEntrySelfS0240, FNote, FEntrySelfS0258, '
                   'FEntrySelfS0248, FEntrySelfS0239, FEntrySelfS0244, FEntrySelfS0263',
        post_process=_post_code_4,
    ),
    5: EntryConfig(
        columns=['采购订单', 'TTY新料号', '产品名称', '宽', '型号', '规格', '支', '长', '数量', '批号'],
        sql_fields='FEntrySelfS0239, FEntrySelfS0258, FEntrySelfS0257, FEntrySelfS0241, '
                   'FNote, FEntrySelfS0240, FEntrySelfS0243, FEntrySelfS0242, FEntrySelfS0244, FEntrySelfS0248',
        post_process=_post_code_5_6,
    ),
    6: EntryConfig(
        columns=['采购订单', 'TTY新料号', '产品名称', '宽', '型号', '规格', '支', '长', '数量', '批号'],
        sql_fields='FEntrySelfS0239, FEntrySelfS0258, FEntrySelfS0257, FEntrySelfS0241, '
                   'FNote, FEntrySelfS0240, FEntrySelfS0243, FEntrySelfS0242, FEntrySelfS0244, FEntrySelfS0248',
        post_process=_post_code_5_6,
    ),
}


# ===== 核心查询函数 =====
def _query_entry(cursor, finter_id: int, code_name: int) -> pd.DataFrame:
    """根据 code_name 查询送货单明细（通用实现）"""
    config = ENTRY_CONFIGS.get(code_name)
    if not config:
        logger.warning(f"未知的 codeName: {code_name}")
        return pd.DataFrame()

    sql = (f"SELECT {config.sql_fields} "
           f"FROM {DB_SCHEMA_2019}.SEOutStockEntry WHERE FInterID = ?")
    cursor.execute(sql, finter_id)
    rows = cursor.fetchall()
    if not rows:
        return pd.DataFrame()

    # 直接用 pyodbc.Row → DataFrame，避免二次转换
    df = pd.DataFrame.from_records(rows, columns=config.columns)

    if config.post_process:
        df = config.post_process(df)

    df.reset_index(drop=False, inplace=True)
    df.index.name = 'ID'
    return df


def query_SEord(params: str, code_name: int) -> pd.DataFrame:
    """查询送货单：先查表头获取 FInterID，再查明细"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {', '.join(COLUMNS_SEOUTSTOCK)} "
                f"FROM {DB_SCHEMA_2019}.SEOutStock WHERE FBILLNO = ?",
                params
            )
            rows = cursor.fetchall()
            if not rows:
                logger.warning(f"未找到送货单，单号: {params}")
                return pd.DataFrame()

            finter_id = rows[0][0]
            return _query_entry(cursor, finter_id, code_name)

    except Exception as e:
        logger.error(f'query_SEord 出错 (单号={params}, code={code_name}): {e}', exc_info=True)
        return pd.DataFrame()


# ===== 物料查询（通用函数替代两个重复函数）=====
def _query_material(params: str, schema: str) -> pd.DataFrame:
    """通用物料查询，schema 参数区分不同数据库"""
    like_param = f'%{params}%'
    sql = f"""
        SELECT t1.FName, t1.FModel, t1.FNumber, t1.FShortNumber, t1.FItemID, t3.FName AS FUnitName
        FROM {schema}.t_ICItemCore t1
        JOIN {schema}.t_ICItemBase t2 ON t1.FItemID = t2.FItemID
        JOIN {schema}.t_MeasureUnit t3 ON t2.FUnitID = t3.FMeasureUnitID
        WHERE t1.FNAME LIKE ? OR t1.FModel LIKE ? OR t1.FNumber LIKE ?
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, like_param, like_param, like_param)
            rows = cursor.fetchall()
            if not rows:
                logger.warning(f'物料查询结果为空: {params}')
                return pd.DataFrame()

            columns = ['物料名称', '规格型号', '物料代码', '短代码', '内码', '单位']
            df = pd.DataFrame.from_records(rows, columns=columns)
            return df
    except Exception as e:
        logger.error(f'_query_material 出错: {e}', exc_info=True)
        return pd.DataFrame()


def queryMaterial(params: str) -> pd.DataFrame:
    """查询 2019 数据库物料"""
    return _query_material(params, DB_SCHEMA_2019)


def LSMqueryMaterial(params: str) -> pd.DataFrame:
    """查询 2023 数据库物料"""
    return _query_material(params, DB_SCHEMA_2023)


# ===== 主函数（测试用）=====
if __name__ == "__main__":
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    handler = RotatingFileHandler(
        os.path.join(log_dir, 'server_connect.log'),
        maxBytes=10485760, backupCount=5
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)

    # 测试 query_SEord
    df = query_SEord('JHS0172378', 5)
    print("query_SEord 结果:" if not df.empty else "query_SEord 未返回数据。")
    if not df.empty:
        print(df)

    # 测试物料查询
    for name, func in [('queryMaterial', queryMaterial),
                       ('LSMqueryMaterial', LSMqueryMaterial)]:
        df_m = func('物料')
        print(f"\n{name} 结果:" if not df_m.empty else f"\n{name} 未返回数据。")
        if not df_m.empty:
            print(df_m.head())