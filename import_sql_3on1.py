# -*- coding: UTF-8 -*-
import numpy as np
import chardet
import pandas as pd
import calendar
import datetime
import time
import re
import sqlalchemy.types as t
from sqlalchemy import create_engine


pd.set_option("display.max_columns", 5000)
pd.set_option("display.width", 5000)

engine = create_engine("mssql+pymssql://(local)/Internal_sales")

df = pd.read_excel(open("三合一销售报表/2022/三合一表2月终版.xlsx", "rb"), sheet_name="三合一表_导出版")  # 从Excel读取数
print("Finished data reading...")

df.columns = [
    "YEAR",
    "DATE",
    "MONTH",
    "QUARTER",
    "HP_ID",
    "HP_NAME",
    "STORE_ID",
    "STORE_NAME",
    "PROVINCE",
    "CITY",
    "COUNTY",
    "LEVEL",
    "IF_COMMUNITY",
    "IF_DUALCALL",
    "PRODUCT",
    "STRENGTH",
    "TAG",
    "VOLUME",
    "VOLUME_STD",
    "VALUE",
    "BU",
    "RD",
    "RM",
    "DSM",
    "RSP",
    "PRODUCT_GROUP_RM",
    "PRODUCT_GROUP_DSM",
    "PRODUCT_GROUP_RSP",
    "RM_ID",
    "RM_NAME",
    "RM_NOTE",
    "DSM_ID",
    "DSM_NAME",
    "DSM_NOTE",
    "RSP_ID",
    "RSP_NAME",
    "RSP_NOTE",
    # "PRODUCT_GROUP", # 2021年2月终版时OA原始数据文件删除了此字段
    "GPO",
    "HP_TYPE",
]

mask = df["IF_COMMUNITY"] == "Y"
df.loc[mask, "IF_COMMUNITY"] = True
df.loc[~mask, "IF_COMMUNITY"] = False

mask = df["IF_DUALCALL"] == 1
df.loc[mask, "IF_DUALCALL"] = True
df.loc[~mask, "IF_DUALCALL"] = False

df["DATE"] = df["DATE"] * 100 + 1
df["DATE"] = pd.to_datetime(df["DATE"], format="%Y%m%d")

df['HOSPITAL'] = df['HP_ID'] + " " + df['HP_NAME']
df['STORE'] = df['STORE_ID'] + " " + df['STORE_NAME']
df['RM_POS_NAME'] = df['RM'] + " " + df['RM_NAME']
df['DSM_POS_NAME'] = df['DSM'] + " " + df['DSM_NAME']
df['RSP_POS_NAME'] = df['RSP'] + " " + df['RSP_NAME']
print(df)

print("start importing...")
df.to_sql(
    "sales",
    con=engine,
    if_exists="replace",
    index=False,
    dtype={
        "YEAR": t.INTEGER(),
        "DATE": t.DateTime(),
        "MONTH": t.INTEGER(),
        "QUARTER": t.INTEGER(),
        "HP_ID": t.NVARCHAR(length=10),
        "HP_NAME": t.NVARCHAR(length=100),
        "HOSPITAL": t.NVARCHAR(length=110),
        "STORE_ID": t.NVARCHAR(length=10),
        "STORE_NAME": t.NVARCHAR(length=100),
        "STORE": t.NVARCHAR(length=110),
        "PROVINCE": t.NVARCHAR(length=3),
        "CITY": t.NVARCHAR(length=30),
        "COUNTY": t.NVARCHAR(length=30),
        "LEVEL": t.NVARCHAR(length=4),
        "IF_COMMUNITY": t.Boolean(),
        "IF_DUALCALL": t.Boolean(),
        "PRODUCT": t.NVARCHAR(length=10),
        "STRENGTH": t.NVARCHAR(length=10),
        "TAG": t.NVARCHAR(length=4),
        "VOLUME": t.FLOAT(),
        "VOLUME_STD": t.FLOAT(),
        "VALUE": t.FLOAT(),
        "BU": t.NVARCHAR(length=10),
        "RD": t.NVARCHAR(length=10),
        "RM": t.NVARCHAR(length=20),
        "RM_POS_NAME": t.NVARCHAR(length=40),
        "DSM": t.NVARCHAR(length=20),
        "DSM_POS_NAME": t.NVARCHAR(length=40),
        "RSP": t.NVARCHAR(length=20),
        "RSP_POS_NAME": t.NVARCHAR(length=40),
        "PRODUCT_GROUP_RM": t.NVARCHAR(length=10),
        "PRODUCT_GROUP_DSM": t.NVARCHAR(length=10),
        "PRODUCT_GROUP_RSP": t.NVARCHAR(length=10),
        "RM_ID": t.NVARCHAR(length=20),
        "RM_NAME": t.NVARCHAR(length=20),
        "RM_NOTE": t.NVARCHAR(length=20),
        "DSM_ID": t.NVARCHAR(length=20),
        "DSM_NAME": t.NVARCHAR(length=20),
        "DSM_NOTE": t.NVARCHAR(length=20),
        "RSP_ID": t.NVARCHAR(length=20),
        "RSP_NAME": t.NVARCHAR(length=20),
        "RSP_NOTE": t.NVARCHAR(length=20),
        # "PRODUCT_GROUP": t.NVARCHAR(length=10), # 2021年2月终版时OA原始数据文件删除了此字段
        "GPO": t.NVARCHAR(length=20),
        "HP_TYPE": t.NVARCHAR(length=20),
    },
)

print(time.process_time())
