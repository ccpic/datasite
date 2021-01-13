from django.shortcuts import render, HttpResponse
from sqlalchemy import create_engine
import pandas as pd
import json
import numpy as np
from .models import *
import six

ENGINE = create_engine("mssql+pymssql://(local)/Internal_sales")  # 创建数据库连接引擎
DB_TABLE = "data"

# 该字典为数据库字段名和Django Model的关联
D_MODEL = {
    "PROVINCE": Province,
    "CITY": City,
    "COUNTY": County,
}


# 该字典key为前端准备显示的所有多选字段名, value为数据库对应的字段名
D_MULTI_SELECT = {
    "省份": "PROVINCE",
    "城市": "CITY",
    "区县": "COUNTY",
}


def index(request):
    mselect_dict = {}
    for key, value in D_MULTI_SELECT.items():
        mselect_dict[key] = {}
        mselect_dict[key]["select"] = value

    context = {"mselect_dict": mselect_dict}
    return render(request, "internal_sales/display.html", context)


def query(request):
    form_dict = dict(six.iterlists(request.GET))
    df = get_df(form_dict)

    table = get_ptable_monthly(df)
    ptable_monthly = table.to_html(
        escape=False,
        formatters=build_formatters_by_col(table),  # 逐列调整表格内数字格式
        classes="ui selectable celled table",  # 指定表格css class为Semantic UI主题
        table_id="ptable_monthly",  # 指定表格id
    )

    context = {"ptable_monthly": ptable_monthly}

    return HttpResponse(
        json.dumps(context, ensure_ascii=False), content_type="application/json charset=utf-8",
    )  # 返回结果必须是json格式


def get_ptable_monthly(df):
    df_ptable = df[df.index >= 202001].T
    df_ptable.fillna(0, inplace=True)
    df_ptable["趋势"] = None

    return df_ptable


def get_df(form_dict, tag="销量", is_pivoted=True):
    sql = sqlparse(form_dict)  # sql拼接
    print(sql)
    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe

    df = df[df.TAG == tag]  # 区分销售、药房销售和指标

    if is_pivoted is True:
        dimension_selected = form_dict["DIMENSION_select"][0]  # 分析维度
        unit_selected = form_dict["UNIT_select"][0]  # 单位（盒数、标准盒数、金额）
        if dimension_selected[0] == "[":

            column = dimension_selected[1:][:-1]
        else:
            column = dimension_selected

        pivoted = pd.pivot_table(
            df,
            values=unit_selected,  # 数据透视汇总值为AMOUNT字段，一般保持不变
            index="DATE",  # 数据透视行为DATE字段，一般保持不变
            columns=column,  # 数据透视列为前端选择的分析维度
            aggfunc=np.sum,
        )  # 数据透视汇总方式为求和，一般保持不变
        if pivoted.empty is False:
            pivoted.sort_values(by=pivoted.index[-1], axis=1, ascending=False, inplace=True)  # 结果按照最后一个DATE表现排序

        pivoted = pd.DataFrame(pivoted.to_records())
        pivoted.set_index("DATE", inplace=True)

        return pivoted
    else:
        return df


def sqlparse(context):
    print(context)
    sql = "Select * from %s WHERE 1=1" % DB_TABLE  # 先处理单选部分
    print(context["customized_sql"])
    if context["customized_sql"][0] == "":
        # 如果前端没有输入自定义sql，直接循环处理多选部分进行sql拼接
        for k, v in context.items():
            if k not in [
                "csrfmiddlewaretoken",
                "DIMENSION_select",
                "PERIOD_select",
                "UNIT_select",
                "lang",
                "toggle_bubble_perf",
                "toggle_treemap_share",
                "customized_sql",
            ]:
                if k[-2:] == "[]":
                    field_name = k[:-9]  # 如果键以[]结尾，删除_select[]取原字段名
                else:
                    field_name = k[:-7]  # 如果键不以[]结尾，删除_select取原字段名
                selected = v  # 选择项
                sql = sql_extent(sql, field_name, selected)  # 未来可以通过进一步拼接字符串动态扩展sql语句
    else:
        sql = context["customized_sql"][0]  # 如果前端输入了自定义sql，忽略前端其他参数直接处理
    return sql


def sql_extent(sql, field_name, selected, operator=" AND "):
    if selected is not None:
        statement = ""
        for data in selected:
            statement = statement + "'" + data + "', "
        statement = statement[:-2]
        if statement != "":
            sql = sql + operator + field_name + " in (" + statement + ")"
    return sql


def search(request, column, kw):
    # sql = "SELECT DISTINCT TOP 20 %s FROM %s WHERE %s like '%%%s%%'" % (column, DB_TABLE, column, kw) # 返回不重复的前20个结果
    try:
        # df = pd.read_sql_query(sql, ENGINE)
        # l = df.values.flatten().tolist()
        m = D_MODEL[column]
        results = m.objects.filter(name__contains=kw)
        l = results.values_list("name")
        print(l)
        results_list = []
        for item in l:
            option_dict = {
                "name": item,
                "value": item,
            }
            results_list.append(option_dict)
        res = {
            "success": True,
            "results": results_list,
            "code": 200,
        }
    except Exception as e:
        res = {
            "success": False,
            "errMsg": e,
            "code": 0,
        }
    return HttpResponse(
        json.dumps(res, ensure_ascii=False), content_type="application/json charset=utf-8",
    )  # 返回结果必须是json格式


def build_formatters_by_col(df):
    format_abs = lambda x: "{:,.0f}".format(x)
    format_share = lambda x: "{:.1%}".format(x)
    format_gr = lambda x: "{:.1%}".format(x)
    format_currency = lambda x: "¥{:,.1f}".format(x)
    d = {}
    for column in df.columns:
        if "份额" in str(column) or "贡献" in str(column):
            d[column] = format_share
        elif "价格" in str(column) or "单价" in str(column):
            d[column] = format_currency
        elif "同比增长" in str(column) or "增长率" in str(column) or "CAGR" in str(column) or "同比变化" in str(column):
            d[column] = format_gr
        elif "趋势" in str(column):
            d[column] = None
        else:
            d[column] = format_abs

    return d
