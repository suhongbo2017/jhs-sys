import pandas as pd
import os
from sqlalchemy import create_engine
import mysql.connector # 确保导入 mysql.connector

# 连接参数
def get_mysql_engine():
    user = os.getenv('MYSQL_USER', 'su')
    password = os.getenv('MYSQL_PASSWORD', '123456')
    host = os.getenv('MYSQL_HOST', '192.168.0.118')
    database = os.getenv('MYSQL_DATABASE', 'material_table')
    
    # 使用 f-string 格式化连接字符串
    engine = create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{database}')
    return engine

# 写入函数
def write_to_mysql(df: pd.DataFrame, table_name: str):
    df.index.name = "id"
    print(df.index)

    # 使用 get_mysql_engine() 获取引擎对象
    df.to_sql(name=table_name, con=get_mysql_engine(), if_exists='replace', index_label='id')
    print(f"数据已成功写入到 MySQL 表 '{table_name}'")

if __name__ == "__main__":
    # 示例用法：创建一个示例 DataFrame 并写入 MySQL
    # 注意：在实际使用中，'clearData.xlsx' 应该存在或从其他来源获取数据
    try:
        # 假设 clearData.xlsx 存在，或者创建一个示例 DataFrame
        # df_to_write = pd.read_excel('clearData.xlsx')
        
        # 创建一个示例 DataFrame
        data = {'col1': [1, 2], 'col2': ['A', 'B']}
        df_to_write = pd.DataFrame(data)
        
        table_name = 'production_schedule_test' # 使用一个测试表名
        write_to_mysql(df_to_write, table_name)
    except Exception as e:
        print(f"写入 MySQL 发生错误: {e}")
