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

df = pd.read_excel(open("potential.xlsx", "rb"), sheet_name="potential")  # 从Excel读取数
print("Finished data reading...")

df.columns = [
    "HP_ID",
    "HP_NAME",
    "PROVINCE",
    "CITY",
    "COUNTY",
    "POTENTIAL_DOT",
    "DATA_SOURCE",
    "HP_TYPE",
    "SALES_MAT",
    "RSP",
    "TARGET",
    "BU",
    "RD",
    "RM",
    "DSM",
    "SALES_COND",
    "DECILE",
]

df["HOSPITAL"] = df["HP_ID"] + " " + df["HP_NAME"]

print("start importing...")
df.to_sql(
    "potential",
    con=engine,
    if_exists="replace",
    index=False,
    dtype={
        "HP_ID": t.NVARCHAR(length=10),
        "HP_NAME": t.NVARCHAR(length=100),
        "HOSPITAL": t.NVARCHAR(length=110),
        "PROVINCE": t.NVARCHAR(length=3),
        "CITY": t.NVARCHAR(length=30),
        "COUNTY": t.NVARCHAR(length=30),
        "POTENTIAL_DOT": t.FLOAT(),
        "DATA_SOURCE": t.NVARCHAR(length=30),
        "HP_TYPE": t.NVARCHAR(length=4),
        "SALES_MAT": t.FLOAT(),
        "RSP": t.NVARCHAR(length=100),
        "TARGET": t.FLOAT(),
        "BU": t.NVARCHAR(length=10),
        "RD": t.NVARCHAR(length=10),
        "RM": t.NVARCHAR(length=30),
        "DSM": t.NVARCHAR(length=30),
        "SALES_COND": t.NVARCHAR(length=10),
        "DECILE": t.INTEGER(),
    },
)

print(time.process_time())
