# import pandas as pd
from sqlalchemy import create_engine
# import mysql.connector

# df= pd.read_excel('clearData.xlsx')

#连接参数
def engine():
       user= 'su'
       password= '123456'
       host= '192.168.0.118'
       database= 'material_table'
       engine= create_engine(f'mysql+mysqlconnector://{user}:{password}@{host}/{database}')
       return engine


#写入函数
# def write_mysql():
       
#        df.index.name = "id"
#        print(df.index)

#        table_name= 'production_schedule'

#        df.to_sql(name=table_name,con=engine,if_exists='replace',index_label='id')

