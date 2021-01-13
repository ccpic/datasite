from django.shortcuts import render, HttpResponse
from sqlalchemy import create_engine
import pandas as pd
import json
import numpy as np
from .models import *
import six
import datetime

ENGINE = create_engine("mssql+pymssql://(local)/Internal_sales")  # 创建数据库连接引擎
DB_TABLE = "data"
date = datetime.datetime(year=2020,month=11,day=1)
date_ya = date.replace(year=date.year-1)  # 同比月份
date_year_begin = date.replace(month=1)   # 本年度开头
date_ya_begin = date_ya.replace(month=1)   # 去年开头

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
    df_sales = get_df(form_dict)
    df_target = get_df(form_dict, "指标")

    table = get_ptable_monthly(df_sales)
    ptable_monthly = table.to_html(
        escape=False,
        formatters=build_formatters_by_col(table),  # 逐列调整表格内数字格式
        classes="ui selectable celled table",  # 指定表格css class为Semantic UI主题
        table_id="ptable_monthly",  # 指定表格id
    )

    kpi = get_kpi(df_sales, df_target)

    context = {"ptable_monthly": ptable_monthly,
               }

    context = dict(context, **kpi)

    return HttpResponse(
        json.dumps(context, ensure_ascii=False), content_type="application/json charset=utf-8",
    )  # 返回结果必须是json格式


def get_ptable_monthly(df):
    df_ptable = df[df.index >= date_year_begin].T
    df_ptable.fillna(0, inplace=True)
    df_ptable["趋势"] = None  # 表格最右侧预留Sparkline空列

    return df_ptable


def get_kpi(df_sales, df_target):
    kpi = {}

    for period in ['ytd', 'mon']:
        # 按列求和为查询总销售的Series
        sales_total = df_sales.sum(axis=1)
        # YTD销售
        sales = sales_total.loc[date_mask(df_sales,period)[0]].sum()
        # YTDYA销售
        sales_ya = sales_total.loc[date_mask(df_sales,period)[1]].sum()
        # YTD同比增长
        sales_gr = sales / sales_ya - 1

        # 按列求和为查询总指标的Series
        target_total = df_target.sum(axis=1)
        print(target_total)
        # YTD指标
        target = target_total.loc[date_mask(df_target,period)[0]].sum()
        # YTD达标率
        ach = sales / target

        kpi = dict(kpi,
                   **{"sales_%s" % period: int(sales),
                      "sales_gr_%s" % period: sales_gr,
                      "target_%s" % period: int(target),
                      "ach_%s" % period: ach,
                      }
                   )

    print(kpi)

    return kpi


def date_mask(df, period):
    if period == 'ytd':
        mask = (df.index >= date_year_begin) & (df.index <= date)
        mask_ya = (df.index >= date_ya_begin) & (df.index <= date_ya)
    elif period == 'mon':
        mask = (df.index == date)
        mask_ya = (df.index == date_ya)

    return  mask, mask_ya


def get_df(form_dict, tag="销售", is_pivoted=True):
    sql = sqlparse(form_dict)  # sql拼接
    print(sql)
    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe

    # 区分销售和指标
    if tag=="销售":
        df = df[df.TAG != "指标"]
    else:
        df = df[df.TAG == "指标"]

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
