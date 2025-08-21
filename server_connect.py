'''本函数是对金蝶数据库中的送货单表头和表体进行查询，得到分列的数据进行汇总后返回。'''

import pyodbc
import pandas as pd
import os

# 从环境变量获取数据库配置
server = os.getenv('DB_SERVER', '192.168.0.234')
database = os.getenv('DB_DATABASE', 'AIS20191210135722')
username = os.getenv('DB_USERNAME', 'sa')
password = os.getenv('DB_PASSWORD', 'Jhs16888')
DSN = 'seord'

def get_connection():
    """获取数据库连接"""
    try:
        connection_string = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};trustServerCertificate=yes;'
        return pyodbc.connect(connection_string)
    except Exception as e:
        print(f"数据库连接错误: {e}")
        raise

# 创建全局连接
conn = get_connection()

# 查询送货单表头数据
def query_SEord(params,codeName):
# 使用try防止异常
    cursor = None
    try:
        global conn
        if conn is None or conn.closed:
            conn = get_connection()
        cursor = conn.cursor()
        # 查询语句
        
        sql= f"SELECT FInterID, FBillNo, FTranType, FSalType, FCustID FROM AIS20191210135722.dbo.SEOutStock WHERE FBILLNO = ?"
        print()
        # 执行查询或其他数据库操作
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        # print(rows)
        data=[]
        # 打印结果
        for row in rows:
            data.append(row)

        # 返回查询结果
    
        cursor = conn.cursor()
        # 查询语句
        if codeName == 1:
            sql1= f"SELECT FEntrySelfS0257, FEntrySelfS0240,FEntrySelfS0258,FEntrySelfS0248,FEntrySelfS0239,FEntrySelfS0244, FEntrySelfS0263 FROM AIS20191210135722.dbo.SEOutStockEntry WHERE FInterID = ?"

            # 执行查询或其他数据库操作
            cursor.execute(sql1, data[0][0])
            rows1 = cursor.fetchall()
            # 使用
            data1=[[j for j in i] for i in rows1]


            # 关闭连接
            # print(data)
            columns=['物料名称','整支规格','料号','批号','订单号','数量','备注']
            dfs= pd.DataFrame(data1,columns=columns)


            # 使用numpy把decimal格式的数字精度控制在2位。
            dfs['数量']= dfs['数量'].apply(float).round(2)
            # 使用JOIN对合并的备注进行拼接处理得到要求的字符串
            dfs['备注']= dfs['备注'].apply(lambda x: ('*'.join(x.split('*')[-3::2]).replace('M','')+ ' '))
            print(dfs['备注'])

            #对结果进行分类汇总
            dfs= dfs.groupby('物料名称').agg({'整支规格':'first','料号':'first','批号':'first','订单号':'first','数量':'sum','备注':'sum'})
            dfs['数量']= dfs['数量'].apply(float).round(2)
            #新建index名称是ID
            dfs.reset_index(drop=False,inplace=True)
            dfs.index.name= 'ID'

            #返回数据
            
            return dfs
        
        elif codeName == 2:
            sql2= f"SELECT * FROM AIS20191210135722.dbo.SEOutStockEntry WHERE FINTERID  = ?"

            # 执行查询或其他数据库操作
            cursor.execute(sql2, data[0][0])
            rows1 = cursor.fetchall()
            print(rows1)
            data1=[[j for j in i] for i in rows1]

            # print(data1)
            columns=['物料名称','备注','料号','批号','订单号','数量','整支规格']
            dfs= pd.DataFrame(data1)

            print('df',dfs)
            # 使用numpy把decimal格式的数字精度控制在2位。
            # dfs['数量']= dfs['数量'].apply(float).round(2)
            # 使用JOIN对合并的备注进行拼接处理得到要求的字符串
            # dfs['备注']= dfs['备注'].apply(lambda x: ('*'.join(x.split('*')[-3::2]).replace('M','')+ ' '))
            # print(dfs['备注'])

            #对结果进行分类汇总
            # dfs= dfs.groupby('整支规格').agg({'物料名称':'first','料号':'first','批号':'first','订单号':'first','数量':'sum','备注':'sum'})
            # dfs['FEntrySelfS0244']= dfs['FEntrySelfS0244'].apply(float).round(2)
            #新建index名称是ID
            dfs.reset_index(drop=False,inplace=True)
            dfs.index.name= 'ID'

            #返回数据
            return dfs        

        elif codeName == 3:
            sql3= f"SELECT FEntrySelfS0239, FEntrySelfS0258,FEntrySelfS0257,FEntrySelfS0241,FEntrySelfS0242,FEntrySelfS0243, FEntrySelfS0244, FEntrySelfS0248 FROM AIS20191210135722.dbo.SEOutStockEntry WHERE FInterID = ?"
            # 执行查询或其他数据库操作
            cursor.execute(sql3, data[0][0])
            rows1 = cursor.fetchall()
            # 使用
            data1=[[j for j in i] for i in rows1]


            # 关闭连接
            # print(data)
            columns=['客户订单号','客户品号','客户品名','宽','长','支','数量','批号']
            dfs= pd.DataFrame(data1,columns=columns)


            # 使用numpy把decimal格式的数字精度控制在2位。
            dfs['宽']= dfs['宽'].apply(float).round(2)
            dfs['长']= dfs['长'].apply(float).round(2)
            dfs['支']= dfs['支'].apply(int)
            dfs['数量']= dfs['数量'].apply(float).round(2)
            print('数量的精度',dfs['数量'])
            # 使用JOIN对合并的备注进行拼接处理得到要求的字符串
            # dfs['备注']= dfs['备注'].apply(lambda x: ('*'.join(x.split('*')[-3::2]).replace('M','')+ ' '))
            # print(dfs['备注'])

            #对结果进行分类汇总
            # dfs= dfs.groupby('整支规格').agg({'物料名称':'first','料号':'first','批号':'first','订单号':'first','数量':'sum','备注':'sum'})
            # dfs['数量']= dfs['数量'].apply(float).round(2)
            #新建index名称是ID
            dfs.reset_index(drop=False,inplace=True)
            dfs.index.name= 'ID'

            #返回数据
            return dfs
        elif codeName == 4:
            sql2= f"SELECT FEntrySelfS0257, FEntrySelfS0240,FNote,FEntrySelfS0258,FEntrySelfS0248,FEntrySelfS0239,FEntrySelfS0244, FEntrySelfS0263 FROM AIS20191210135722.dbo.SEOutStockEntry WHERE FInterID = ?"

            # 执行查询或其他数据库操作
            cursor.execute(sql2, data[0][0])
            rows1 = cursor.fetchall()
            # print(rows1)
            data1=[[j for j in i] for i in rows1]

            # print(data)
            columns=['物料名称','备注','批次号','料号','批号','订单号','数量','整支规格']
            dfs= pd.DataFrame(data1,columns=columns)

            # print('df',dfs)
            # 使用numpy把decimal格式的数字精度控制在2位。
            dfs['数量']= dfs['数量'].apply(float).round(2)
            # 使用JOIN对合并的备注进行拼接处理得到要求的字符串
            dfs['整支规格']= dfs['整支规格'].apply(lambda x: '*'.join(str(x).split("*")[1:])+ '+ ')
            print('拼接后的整支\n',dfs['整支规格'])

            #对结果进行分类汇总
            #其中使用join(map(str,x))对整支规格中的数据字符串化再进行拼接。
            dfs= dfs.groupby('物料名称').agg({'整支规格':'sum','料号':'first','批次号':'first','订单号':'first','数量':'sum','备注':'first'})
            dfs['数量']= dfs['数量'].apply(float).round(2)
            #新建index名称是ID
            dfs.reset_index(drop=False,inplace=True)
            dfs.index.name= 'ID'
            print('合并完成的\n',dfs)
            #返回数据
            return dfs    

        elif codeName == 5:
            sql3= f"SELECT FEntrySelfS0239, FEntrySelfS0258,FEntrySelfS0257,FEntrySelfS0241,FNote,FEntrySelfS0240,FEntrySelfS0243,FEntrySelfS0242, FEntrySelfS0244, FEntrySelfS0248 FROM AIS20191210135722.dbo.SEOutStockEntry WHERE FInterID = ?"
            # 执行查询或其他数据库操作
            cursor.execute(sql3, data[0][0])
            rows1 = cursor.fetchall()
            # 使用
            data1=[[j for j in i] for i in rows1]


            # 关闭连接
            # print(data)
            columns=['采购订单','TTY新料号','产品名称','宽','型号','规格','支','长','数量','批号']
            dfs= pd.DataFrame(data1,columns=columns)
            print(dfs)

            # 使用numpy把decimal格式的数字精度控制在2位。
            dfs['宽']= dfs['宽'].apply(int).round(0)
            dfs['长']= dfs['长'].apply(int).round(0)
            dfs['支']= dfs['支'].apply(int).round(0)
            dfs['数量']= dfs['数量'].apply(float).round(2)
            print('数量的精度',dfs['数量'])

            #新建index名称是ID
            dfs.reset_index(drop=False,inplace=True)
            dfs.index.name= 'ID'

            #返回数据
            return dfs   
        elif codeName == 6:
            sql3= f"SELECT FEntrySelfS0239, FEntrySelfS0258,FEntrySelfS0257,FEntrySelfS0241,FNote,FEntrySelfS0240,FEntrySelfS0243,FEntrySelfS0242, FEntrySelfS0244, FEntrySelfS0248 FROM AIS20191210135722.dbo.SEOutStockEntry WHERE FInterID = ?"
            # 执行查询或其他数据库操作
            cursor.execute(sql3, data[0][0])
            rows1 = cursor.fetchall()
            # 使用
            data1=[[j for j in i] for i in rows1]


            # 关闭连接
            # print(data)
            columns=['采购订单','TTY新料号','产品名称','宽','型号','规格','支','长','数量','批号']
            dfs= pd.DataFrame(data1,columns=columns)
            print(dfs)

            # 使用numpy把decimal格式的数字精度控制在2位。
            dfs['宽']= dfs['宽'].apply(int).round(0)
            dfs['长']= dfs['长'].apply(int).round(0)
            dfs['支']= dfs['支'].apply(int).round(0)
            dfs['数量']= dfs['数量'].apply(float).round(2)
            print('数量的精度',dfs['数量'])

            #新建index名称是ID
            dfs.reset_index(drop=False,inplace=True)
            dfs.index.name= 'ID'

            #返回数据
            return dfs   
    except Exception as e:
        print(f'出现错误：{e}')
        return e
    finally:
        if cursor:
            cursor.close()  # 只关闭游标，保持连接

def queryMaterial(params):
    cursor = None
    try:
        global conn
        if conn is None or conn.closed:
            conn = get_connection()
        cursor = conn.cursor()
        # 查询语句
        params= f"%{params}%"
        print('服务器中的params值是',params)

        sql= f"SELECT FName, FModel, FNumber, FShortNumber,FItemID FROM AIS20191210135722.dbo.t_ICItemCore WHERE FNAME LIKE ? or FModel LIKE ? or FNumber LIKE ?; "
        # 执行查询或其他数据库操作
        cursor.execute(sql,params,params,params)

        rows1 = cursor.fetchall()
        if not rows1 :
            print('The query is empty')
            
        # print(1,rows1)
        # 使用
        data1=[[j for j in i] for i in rows1]

        
        # 关闭连接
        # print(data)
        columns=['物料名称','规格型号','物料代码','短代码','内码']
        dfs= pd.DataFrame(data1,columns=columns)
        print('server_messsge',dfs.head())
        #返回数据
        # conn.close()
        return dfs
    except Exception as e:

        print(f'出现错误：{e}')
        conn.close()
        return e
    
    finally:
        if cursor:
            cursor.close()  # 只关闭游标，保持连接

def LSMqueryMaterial(params):
    cursor = None
    try:
        global conn
        if conn is None or conn.closed:
            conn = get_connection()
        cursor = conn.cursor()
        # 查询语句
        params= f"%{params}%"
        print('服务器中的params值是',params)

        sql= f"SELECT FName, FModel, FNumber, FShortNumber,FItemID FROM AIS20230525154804.dbo.t_ICItemCore WHERE FNAME LIKE ? or FModel LIKE ? or FNumber LIKE ?; "
        # 执行查询或其他数据库操作
        cursor.execute(sql,params,params,params)

        rows1 = cursor.fetchall()
        if not rows1 :
            print('The query is empty')
            
        # print(1,rows1)
        # 使用
        data1=[[j for j in i] for i in rows1]

        
        # 关闭连接
        # print(data)
        columns=['物料名称','规格型号','物料代码','短代码','内码']
        dfs= pd.DataFrame(data1,columns=columns)
        print('server_messsge',dfs.head())
        #返回数据
        
        return dfs
    except Exception as e:

        print(f'出现错误：{e}')
        conn.close()
        return e
    finally:
        if cursor:
            cursor.close()  # 只关闭游标，保持连接

# def seorder(startDate,endDate):
#     try:

#         # 创建游标
#         cursor = conn.cursor()
#         # 查询语句
#         # params= f"%{params}%"
#         print('服务器中的params值是',startDate,endDate)
#         sql= f"SELECT FInterID, FItemID, FQty, FPrice, FAmount, FFetchDate, FOrderBillNo, FEntrySelfS0257,FEntrySelfS0248,FEntrySelfS0263 FROM AIS20191210135722.dbo.SEOutStockEntry WHERE CONVERT (DATE,FFETCHDATE)>= ? AND CONVERT (DATE,FFETCHDATE)<= ?;"
#         # sql= f"SELECT FName, FModel, FNumber, FShortNumber,FItemID FROM AIS20230525154804.dbo.t_ICItemCore WHERE FNAME LIKE ? or FModel LIKE ? or FNumber LIKE ?; "
#         # 执行查询或其他数据库操作
#         cursor.execute(sql,(startDate,endDate))

#         rows1 = cursor.fetchall()
#         if not rows1 :
#             print('The query is empty')
            
#         # print(1,rows1)
#         # 使用
#         data1=[[j for j in i] for i in rows1]

        
#         # 关闭连接
#         # print(data)
#         # columns=[]
#         dfs= pd.DataFrame(data1,)
#         print('server_messsge',dfs.head())
#         #返回数据
        
#         return dfs
#     except Exception as e:

#         print(f'出现错误：{e}')
#         conn.close()
#         return e   
#     finally:
#         conn.close()


if __name__ == "__main__":
    df = query_SEord('JHS0172378',5)
    df1 = query_SEord('JHS0172378',5)
    print(df1)
    print(df)
