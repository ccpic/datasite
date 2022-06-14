from enum import unique
from locale import currency
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse
from django.http import request
import pandas as pd
from sqlalchemy import create_engine
import json
from datasite.commons import NpEncoder, qdict_to_dict, get_dt_page
import numpy as np
import simplejson

ENGINE = create_engine("mssql+pymssql://(local)/Roxa")  # 创建数据库连接引擎
DB_TABLE = "sales"


@login_required
def index(request: request) -> HttpResponse:
    """app静态首页

    Parameters
    ----------
    request : request
        django前端默认request，无额外信息

    Returns
    -------
    HttpResponse
        主要包含传往前端数据的字典
    """

    context = {}

    return render(request, "roxa/roxa.html", context)


def province(request: request) -> HttpResponse:
    d_context = qdict_to_dict(request.GET)

    context = {
        "json_province": json.dumps(d_context["province"]),
        "province": d_context["province"],
    }

    return render(request, "roxa/province.html", context)


def city(request: request) -> HttpResponse:
    d_context = qdict_to_dict(request.GET)
    context = {
        "json_province": json.dumps(d_context["province"]),
        "province": d_context["province"],
        "json_city": json.dumps(d_context["city"]),
        "city": d_context["city"],
    }

    return render(request, "roxa/city.html", context)


def query(request: request) -> HttpResponse:
    d_context = qdict_to_dict(request.GET)

    region = d_context.get("province", "全国")
    if region == "全国":
        sql = f"SELECT * FROM {DB_TABLE}"
        index = "PROVINCE"
    else:
        sql = f"SELECT * FROM {DB_TABLE} WHERE PROVINCE = '{region}'"
        index = "CITY"

    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe

    result = get_df(df, index)

    context = {
        "data": result.to_dict(),
        # "value_max": result[metric].max(),
        # "value_min": result[metric].min(),
    }
    return HttpResponse(
        simplejson.dumps(context, ignore_nan=True),
        # json.dumps(context, cls=NpEncoder, allow_nan=True, ensure_ascii=False),
        content_type="application/json charset=utf-8",
    )  # 返回结果必须是json格式


def get_df(df: pd.DataFrame, index: str) -> pd.DataFrame:
    unit = 10000

    pivoted = pd.pivot_table(
        data=df, values="VALUE_TARGET", index=index, columns="DATE", aggfunc=sum
    ).fillna(0)
    pivoted = pd.DataFrame(pivoted.to_records())  # pivot table对象转为默认df
    pivoted.set_index(index, inplace=True)

    # 2021H1指标金额
    target_value = (pivoted.loc[:, ["21Q1", "21Q2"]].sum(axis=1) / unit)

    pivoted = pd.pivot_table(
        data=df, values="VALUE", index=index, columns="DATE", aggfunc=sum
    ).fillna(0)
    pivoted = pd.DataFrame(pivoted.to_records())  # pivot table对象转为默认df
    pivoted.set_index(index, inplace=True)

    pivoted = pivoted.reindex(
        columns=["20Q1", "20Q2", "20Q3", "20Q4", "21Q1", "21Q2"]
    )  # 防止某些列数据缺失影响后续计算
    
    # 2021H1销售额
    value_abs = (pivoted.loc[:, ["21Q1", "21Q2"]].sum(axis=1) / unit)
    print(value_abs)
    # 2021H1达成率
    ach = value_abs.div(target_value)

    # 2021H1销售额同比净增长
    value_diff1 = (
        (
            pivoted.loc[:, ["21Q1", "21Q2"]]
            .sum(axis=1)
            .subtract(pivoted.loc[:, ["20Q1", "20Q2"]].sum(axis=1))
        )
        / unit
    )
    # 2021H1销售额环比净增长
    value_diff2 = (
        (
            pivoted.loc[:, ["21Q1", "21Q2"]]
            .sum(axis=1)
            .subtract(pivoted.loc[:, ["20Q3", "20Q4"]].sum(axis=1))
        )
        / unit
    )
    # 2021H1销售额同比增长率
    value_gr1 = (
        pivoted.loc[:, ["21Q1", "21Q2"]]
        .sum(axis=1)
        .div(pivoted.loc[:, ["20Q1", "20Q2"]].sum(axis=1))
    ) - 1

    # 2021H1销售额环比增长率
    value_gr2 = (
        pivoted.loc[:, ["21Q1", "21Q2"]]
        .sum(axis=1)
        .div(pivoted.loc[:, ["20Q3", "20Q4"]].sum(axis=1))
    ) - 1

    mask = (df["VALUE"] > 0) & (df["DATE"].isin(["21Q1", "21Q2"]))
    df2 = df.loc[mask, :]

    pivoted = pd.pivot_table(
        data=df2, values="HP_ID", index=index, aggfunc=lambda x: len(x.unique()),
    ).fillna(0)
    pivoted = pd.DataFrame(pivoted.to_records())  # pivot table对象转为默认df
    pivoted.set_index(index, inplace=True)

    # 有量医院家数
    hp_count = pivoted
    
    result = pd.concat(
        [
            target_value,
            ach,
            value_abs,
            value_diff1,
            value_gr1,
            value_diff2,
            value_gr2,
            hp_count,
        ],
        axis=1,
    )


    result.columns = [
        "target_value",
        "ach",
        "value_abs",
        "value_diff1",
        "value_gr1",
        "value_diff2",
        "value_gr2",
        "hp_count",
    ]
    result["hp_count"].fillna(0, inplace=True)
    # 有量医院单产
    result["hp_avg_value"] = result["value_abs"].div(result["hp_count"])
    # 2021H1销售额贡献
    result["value_contrib"] = result["value_abs"].div(result["value_abs"].sum())
    # 2021H1指标金额占比
    result["target_value_contrib"] = result["target_value"].div(
        result["target_value"].sum()
    )

    print(result)

    # result.replace([np.inf, -np.inf, np.nan], "null", inplace=True)  # 替换缺失值

    return result


@login_required()
def table_kpi(request: request) -> HttpResponse:
    """根据前端控件的输入使用Ajax异步通信返回为终端明细DataTables表格准备的数据

    Parameters
    ----------
    request : request
        前端控件的输入选择（包括DataTables的配置项如排序和翻页等）

    Returns
    -------
    HttpResponse
        json格式的单家终端表现和DataTables配置项数据
    """

    form_dict = json.loads(request.POST.get("formdata"))

    country = form_dict.get("country")
    province = form_dict.get("province")
    city = form_dict.get("city")

    if country == "中国":
        sql = f"SELECT * FROM {DB_TABLE}"
    elif province is not None:
        sql = f"SELECT * FROM {DB_TABLE} WHERE PROVINCE = '{province}'"
    else:
        sql = f"SELECT * FROM {DB_TABLE} WHERE CITY = '{city}'"

    level = form_dict.get("level")  # 分析维度 - 省还是市

    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe

    # 检查查询是否有数据，如没有，返回null;如有，继续可视化
    if df.empty:
        dataTable = {}
        dataTable["iTotalRecords"] = 0  # 数据总条数
        dataTable["sEcho"] = 0
        dataTable["iTotalDisplayRecords"] = 0  # 显示的条数
        dataTable["aaData"] = []
        return HttpResponse(
            json.dumps(dataTable), content_type="application/json charset=utf-8",
        )

    aodata = json.loads(request.POST.get("aodata"))
    for item in aodata:
        if item["name"] == "sEcho":
            sEcho = int(item["value"])  # 客户端发送的标识

    # 排序字典，前端点击排序的列索引映射到df字段名
    dict_order = {
        0: level,
        1: "target_value",
        2: "target_value_contrib",
        3: "ach",
        4: "value_abs",
        5: "value_contrib",
        6: "value_diff1",
        7: "value_gr1",
        8: "value_diff2",
        9: "value_gr2",
        10: "hp_count",
        11: "hp_avg_value",
    }

    pivoted = get_df(df, level).reset_index()
    pivoted.rename(columns={"index": level}, inplace=True)
    result = get_dt_page(pivoted, aodata, dict_order)

    data = []
    for item in result:
        print(item)
        row = {
            level: item[level],
            "target_value": "{:,.0f}".format(item["target_value"]),
            "target_value_contrib": "{:,.1%}".format(item["target_value_contrib"]),
            "ach": "{:,.0%}".format(item["ach"]),
            "value_abs": "{:,.0f}".format(item["value_abs"]),
            "value_contrib": "{:,.1%}".format(item["value_contrib"]),
            "value_diff1": "{:+,.0f}".format(item["value_diff1"]),
            "value_gr1": "{:+,.0%}".format(item["value_gr1"]),
            "value_diff2": "{:+,.0f}".format(item["value_diff2"]),
            "value_gr2": "{:+,.0%}".format(item["value_gr2"]),
            "hp_count": item["hp_count"],
            "hp_avg_value": "{:,.1f}".format(item["hp_avg_value"]),
        }
        data.append(row)

    dataTable = {}
    dataTable["iTotalRecords"] = pivoted.shape[0]  # 数据总条数
    dataTable["sEcho"] = sEcho + 1
    dataTable["iTotalDisplayRecords"] = pivoted.shape[0]  # 显示的条数
    dataTable["aaData"] = data

    return HttpResponse(json.dumps(dataTable, ensure_ascii=False))
