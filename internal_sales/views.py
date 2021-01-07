from django.shortcuts import render, HttpResponse
from sqlalchemy import create_engine
import pandas as pd
import json
import numpy as np

ENGINE = create_engine("mssql+pymssql://(local)/Internal_sales")  # 创建数据库连接引擎
DB_TABLE = "data"


def index(request):
    sql = "Select * From %s Where TAG = '%s' AND CITY = '%s'" % (DB_TABLE, "销量", "合肥市")
    df = pd.read_sql_query(sql, ENGINE)

    pivoted = pd.pivot_table(
        df,
        values="VALUE",  # 数据透视汇总值为AMOUNT字段，一般保持不变
        index="FILL_DATE",  # 数据透视行为DATE字段，一般保持不变
        columns="HP_NAME",  # 数据透视列为前端选择的分析维度
        aggfunc=np.sum,
    )  # 数据透视汇总方式为求和，一般保持不变

    if pivoted.empty is False:
        pivoted.sort_values(by=pivoted.index[-1], axis=1, ascending=False, inplace=True)  # 结果按照最后一个DATE表现排序

    context = {"sales":pivoted.to_html()}

    return render(request, "internal_sales/display.html", context)
    # return HttpResponse(
    #     json.dumps(context, ensure_ascii=False), content_type="application/json charset=utf-8",
    # )  # 返回结果必须是json格式


def sql_extent(sql, field_name, selected, operator=" AND "):
    if selected is not None:
        statement = ""
        for data in selected:
            statement = statement + "'" + data + "', "
        statement = statement[:-2]
        if statement != "":
            sql = sql + operator + field_name + " in (" + statement + ")"
    return sql