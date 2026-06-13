import pandas as pd
import os
from sqlalchemy import create_engine

# 全局引擎（复用连接池）
_engine = None


def get_mysql_engine():
    """获取 MySQL 引擎（单例，复用连接池）"""
    global _engine
    if _engine is None:
        user = os.getenv('MYSQL_USER', 'su')
        password = os.getenv('MYSQL_PASSWORD', '123456')
        host = os.getenv('MYSQL_HOST', '192.168.0.118')
        database = os.getenv('MYSQL_DATABASE', 'material_table')
        _engine = create_engine(
            f'mysql+mysqlconnector://{user}:{password}@{host}/{database}',
            pool_size=5, max_overflow=10, pool_pre_ping=True
        )
    return _engine


def write_to_mysql(df: pd.DataFrame, table_name: str):
    """将 DataFrame 写入 MySQL 表"""
    engine = get_mysql_engine()
    df.to_sql(name=table_name, con=engine, if_exists='replace', index_label='id')
    print(f"数据已成功写入到 MySQL 表 '{table_name}'（{len(df)} 行）")


if __name__ == "__main__":
    data = {'col1': [1, 2], 'col2': ['A', 'B']}
    df_to_write = pd.DataFrame(data)
    write_to_mysql(df_to_write, 'production_schedule_test')