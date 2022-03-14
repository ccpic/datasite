# -*- coding: UTF-8 -*-
from matplotlib.pyplot import axis
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

# 从Excel读取数
HP_INDEX = 1.1  # 大医院潜力项目早1年半做，放大1.1倍，RAAS市场年增长率6%

# 导入等级医院终端潜力数据
df_hp = pd.read_excel(open("外部潜力数据.xlsx", "rb"), sheet_name="等级医院潜力")  # 从Excel读取大医院潜力数据
df_hp["信立泰医院名称"].fillna(df_hp["IQVIA 医院名称"], inplace=True)  # 没有信立泰名称的copy IQVIA医院名称
df_hp = df_hp.loc[:, ["信立泰医院代码", "信立泰医院名称", "省份", "城市", "区县", "终端潜力值", "等级医院潜力分级"]]
df_hp.columns = ["医院编码", "医院名称", "省份", "城市", "区县", "终端潜力值", "等级医院内部潜力分位"]
df_hp["数据源"] = "IQVIA大医院潜力201909MAT"
df_hp["医院类型"] = "等级医院"
df_hp["终端潜力值"] = df_hp["终端潜力值"] * HP_INDEX  # 放大

# 导入社区医院终端潜力数据
df_cm = pd.read_excel(
    open("外部潜力数据.xlsx", "rb"), sheet_name="社区医院潜力"
)  # 从Excel读取社区医院潜力数据
df_cm = df_cm.loc[:, ["信立泰ID", "终端名称", "省份", "城市", "区县", "潜力值（DOT）", "社区医院潜力分级"]]
df_cm.columns = ["医院编码", "医院名称", "省份", "城市", "区县", "终端潜力值", "社区医院内部潜力分位"]
df_cm["数据源"] = "Pharbers社区医院潜力202103MAT"
df_cm["医院类型"] = "社区医院"

# 删除重复值
df_combined = pd.concat([df_hp, df_cm])
dup_rows = df_combined[df_combined.duplicated(subset=["医院编码"], keep="last")].dropna(
    subset=["医院编码"]
)  # 找出IQVIA和Pharbers数据重复的终端，keep参数=first保留IQVIA的，last保留Pharbers的
# dup_rows.to_csv("dup.csv", encoding="utf-8-sig")
df_hp = df_hp.drop(dup_rows.index)  # drop重复数据
df_combined = pd.concat([df_hp, df_cm])
print("Finished data reading...")

print(df_combined.columns)

df_combined.columns = [
    "HP_ID",
    "HP_NAME",
    "PROVINCE",
    "CITY",
    "COUNTY",
    "POTENTIAL_DOT",
    "DECILE_HP",
    "DATA_SOURCE",
    "HP_TYPE",
    "DECILE_CM",
]

# 增加一个字段合并医院编码和医院名称，有些场合有用
df_combined["HOSPITAL"] = df_combined.apply(
    lambda x: x["HP_ID"] + " " + x["HP_NAME"]
    if pd.isnull(x["HP_ID"] is False)
    else x["HP_NAME"],
    axis=1,
)

# 合并Decile到同一字段，但该Decile并不是合并计算的潜力分位，仍是等级医院和社区医院内的分位，仅为方便使用
df_combined["DECILE"] = df_combined.apply(
    lambda x: x["DECILE_HP"] if x["HP_TYPE"] == "等级医院" else x["DECILE_CM"], axis=1
)

# 计算潜力等级医院和社区医院合并的潜力分位
df_combined.sort_values(by=["POTENTIAL_DOT"], inplace=True)
df_combined["DECILE_TOTAL"] = (
    np.floor(
        df_combined["POTENTIAL_DOT"].cumsum() / df_combined["POTENTIAL_DOT"].sum() * 10
    )
    + 1
).astype("int")

print("start importing...")
df_combined.to_sql(
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
        "DECILE_HP": t.INTEGER(),
        "DECILE_CM": t.INTEGER(),
        "DECILE": t.INTEGER(),
        "DECILE_TOTAL": t.INTEGER(),
    },
)

print(time.process_time())
