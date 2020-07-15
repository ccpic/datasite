from sqlalchemy import create_engine
import pandas as pd


ENGINE = create_engine('mssql+pymssql://(local)/CHPA_1806') #创建数据库连接引擎
DB_TABLE = 'data'

def export():
    sql = "Select * from data" #标准sql语句，此处为测试返回数据库data表的数据条目n，之后可以用python处理字符串的方式动态扩展
    df = pd.read_sql_query(sql, ENGINE) #将sql语句结果读取至Pandas Dataframe
    print(df)
    df.to_pickle('data.pkl')


if __name__ == '__main__':
    export()