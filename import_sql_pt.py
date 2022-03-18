# -*- coding: UTF-8 -*-
from matplotlib.font_manager import json_dump
from matplotlib.pyplot import axis
import numpy as np
import chardet
import pandas as pd
import calendar
import datetime
import time
import re
import sqlalchemy.types as t
from sqlalchemy import create_engine, engine
import json

pd.set_option("display.max_columns", 5000)
pd.set_option("display.width", 5000)


# 上海只有部分社区是真实开户，其他社区有较大处方但是是等级医院处方流转的结果
cm_sh = [
    "H080000044",
    "H080000113",
    "H080000159",
    "H080000177",
    "H080000228",
    "H080000241",
    "H080000243",
    "H080000266",
    "H080000268",
    "H080000277",
    "H080000279",
    "H080000324",
    "H080000332",
    "H080000340",
    "H080000423",
    "H080000566",
    "H080000570",
    "H080000578",
    "H080000626",
    "H080000634",
    "H080000655",
]


def share_cond(share):
    if share < 0.01:
        condition = "信立坦份额<1%"
    elif share < 0.05:
        condition = "信立坦份额1%-5%"
    elif share < 0.1:
        condition = "信立坦份额5%-10%"
    elif share >= 0.1:
        condition = "信立坦份额>10%"
    else:
        condition = "未开户或非目标"

    return condition


def prepare_internal(
    filename_3on1: str, start_month: int, end_month: int
) -> pd.DataFrame:
    df = pd.read_excel(
        f"./三合一销售报表/2022/{filename_3on1}.xlsx", sheet_name="三合一表_导出版"
    )  # 从Excel读取内部三合一销售数据
    df["标准数量"] = df["标准数量"] * 7  # 盒数转化成片数
    mask = df["产品名称"] == "信立坦"

    mask_sales = (
        mask
        & (df.tag.isin(["销量", "药房销量"]))
        & (df["填报日期"].between(start_month, end_month))
    )
    df_sales = df.loc[mask_sales, :]
    df_sales["大区经理"] = df["大区"] + " " + df["大区经理"]  # 坑位号+姓名，下同
    df_sales["地区经理"] = df["地区"] + " " + df["地区经理"]
    df_sales["销售代表"] = df["代表岗位"] + " " + df["销售代表"]

    # 单家终端销售
    pivoted_sales = pd.pivot_table(
        data=df_sales, values="标准数量", index="目标代码", aggfunc=sum
    )

    # 关联代表情况
    pivoted_reps = pd.pivot_table(
        data=df_sales,
        values="销售代表",
        index="目标代码",
        aggfunc=lambda x: x.dropna().unique(),
    )

    # 指标情况
    mask_target = mask & (df.tag.isin(["指标"])) & (df["年"] == int(str(end_month)[:4]))
    df_target = df.loc[mask_target, :]
    pivoted_target = pd.pivot_table(
        data=df_target, values="标准数量", index="目标代码", aggfunc=sum
    )

    # 合并上方各结果
    df_internal = pd.concat([pivoted_sales, pivoted_reps, pivoted_target], axis=1)
    df_internal.reset_index(level=0, inplace=True)
    df_internal.columns = [
        "目标代码",
        "信立坦MAT销量",
        "销售代表",
        "信立坦年度指标",
    ]

    df_internal = pd.merge(
        df_internal,
        df_sales.drop_duplicates(
            subset=["目标代码", "事业部", "区域", "大区经理", "地区经理"], keep="last"
        )[["目标代码", "事业部", "区域", "大区经理", "地区经理"]],
        on="目标代码",
        how="left",
    )

    df_internal.columns = [
        "医院编码",
        "信立坦MAT销量",
        "销售代表",
        "信立坦年度指标",
        "事业部",
        "区域",
        "大区经理",
        "地区经理",
    ]

    print(df_internal)
    return df_internal


def prepare_potential(hp_index: float) -> pd.DataFrame:

    # 导入等级医院终端潜力数据
    df_hp = pd.read_excel(
        open("外部潜力数据.xlsx", "rb"), sheet_name="等级医院潜力"
    )  # 从Excel读取大医院潜力数据
    df_hp["信立泰医院名称"].fillna(df_hp["IQVIA 医院名称"], inplace=True)  # 没有信立泰名称的copy IQVIA医院名称
    df_hp = df_hp.loc[:, ["信立泰医院代码", "信立泰医院名称", "省份", "城市", "区县", "终端潜力值", "等级医院潜力分级"]]
    df_hp.columns = ["医院编码", "医院名称", "省份", "城市", "区县", "终端潜力值", "等级医院内部潜力分位"]
    df_hp["数据源"] = "IQVIA大医院潜力201909MAT"
    df_hp["医院类型"] = "等级医院"
    df_hp["终端潜力值"] = df_hp["终端潜力值"] * hp_index  # 放大

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

    print(df_combined)
    return df_combined


def merge_data(df_internal: pd.DataFrame, df_potential: pd.DataFrame) -> pd.DataFrame:
    # 准备内部销售数据并merge，left表示以潜力数据为主体匹配
    df_combined = pd.merge(
        left=df_potential, right=df_internal, how="left", on="医院编码"
    )  #

    # 根据是否有医院编码以及是否有销量标记终端销售状态
    df_combined["销售状态"] = df_combined.apply(
        lambda row: "非目标医院"
        if pd.isna(row["信立坦年度指标"]) and pd.isna(row["信立坦MAT销量"])
        else (
            "无销量目标医院"
            if (
                pd.isna(row["信立坦MAT销量"])  # 无销量终端
                or row["信立坦MAT销量"] == 0  # 销量为0
                or (
                    row["省份"] == "上海"
                    and row["医院类型"] == "社区医院"
                    and row["医院编码"] not in cm_sh
                )
            )  # 上海非真正开户的（中心），有销量但为大医院处方延续
            else "有销量目标医院"
        ),
        axis=1,
    )

    mask = df_combined["销售状态"] == "无销量目标医院"  # 因为上海的问题会有一些医院被标为无销量医院，但销量字段>0
    df_combined.loc[mask, "信立坦MAT销量"] = 0

    # # 根据医院名称划分中医院
    # df_combined["中医院"] = df_combined["医院名称"].apply(
    #     lambda x: "中医院" if ("中医" in x or "中西医" in x) and x != "北大医疗鲁中医院" else "非中医院"
    # )

    # 计算终端信立坦销售份额
    df_combined["信立坦销售份额"] = df_combined["信立坦MAT销量"] / df_combined["终端潜力值"]
    df_combined["信立坦销售表现"] = df_combined["信立坦销售份额"].apply(lambda x: share_cond(x))

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
        "MAT_SALES",
        "RSP",
        "ANNUAL_TARGET",
        "BU",
        "RD",
        "RM",
        "AM",
        "STATUS",
        "SHARE",
        "SHARE_GROUP",
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
            df_combined["POTENTIAL_DOT"].cumsum()
            / df_combined["POTENTIAL_DOT"].sum()
            * 10
        )
        + 1
    ).astype("int")
    df_combined.sort_values(by=["POTENTIAL_DOT"], ascending=False, inplace=True)

    # for col in [
    #     "MAT_SALES",
    #     "RSP",
    #     "ANNUAL_TARGET",
    #     "BU",
    #     "RD",
    #     "RM",
    #     "AM",
    #     "STATUS",
    #     "SHARE",
    #     "SHARE_GROUP",
    # ]:
    #     print(col, df_combined[col].astype(str).str.len().max())
    print("Finish Data Reading...")
    return df_combined


def import_data(
    df: pd.DataFrame, engine: engine, table: str,
):
    print("start importing...")
    df.replace([np.inf, -np.inf], np.nan, inplace=True)  # 因分母为0除法产生的inf和-inf替换成nan
    df["RSP"] = df["RSP"].apply(
        lambda x: ",".join(x.tolist()) if type(x) != str and type(x) != float else x
    )  # RSP字段转为字符串存储
    df.loc[:, ["POTENTIAL_DOT", "MAT_SALES", "SHARE"]].fillna(0)  # 数值字段的空值都替换为0
    
    df.to_sql(
        table,
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
            "MAT_SALES": t.FLOAT(),
            "ANNUAL_TARGET": t.FLOAT(),
            "RSP": t.NVARCHAR(length=100),
            "BU": t.NVARCHAR(length=3),
            "RD": t.NVARCHAR(length=3),
            "RM": t.NVARCHAR(length=20),
            "AM": t.NVARCHAR(length=20),
            "STATUS": t.NVARCHAR(length=7),
            "SHARE": t.FLOAT(),
            "SHARE_GROUP": t.NVARCHAR(length=11),
        },
    )


if __name__ == "__main__":
    engine = create_engine("mssql+pymssql://(local)/Internal_sales")
    table = "potential"

    filename_3on1 = "三合一表2月初版"
    start_month = 202103
    end_month = 202202
    HP_INDEX = 1.1  # 大医院潜力项目早1年半做，放大1.1倍，RAAS市场年增长率6%

    df_internal = prepare_internal(filename_3on1, start_month, end_month)
    df_potential = prepare_potential(HP_INDEX)
    df_merged = merge_data(df_internal, df_potential)
    import_data(df_merged, engine, table)
    print(time.process_time())
