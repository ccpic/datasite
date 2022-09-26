from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from sqlalchemy import create_engine
import pandas as pd
import json
import numpy as np
from .models import *
import datetime
from dateutil.relativedelta import relativedelta
from chpa_data.charts import *
from datasite.commons import (
    format_table,
    get_distinct_list,
    sql_extent,
    qdict_to_dict,
    date_mask,
)

try:
    from io import BytesIO as IO  # for modern python
except ImportError:
    from io import StringIO as IO  # for legacy python

ENGINE = create_engine("mssql+pymssql://(local)/Internal_sales")  # 创建数据库连接引擎
DB_TABLE = "retail"
DATE = datetime.datetime(year=2022, month=7, day=1)  # 目标分析月份


# 该字典key为前端准备显示的所有多选字段名, value为数据库对应的字段名
D_MULTI_SELECT = {
    "零售/电商": "BU",
    "产品": "PRODUCT",
    "省份": "PROVINCE",
    "城市": "CITY",
    "大区经理": "RM_POS_NAME",
    "地区经理": "DSM_POS_NAME",
    "代表": "RSP_POS_NAME",
    "客户": "CLIENT",
}

# 该字典为数据分析的不同时间区间维度，键为其完完整命名，值为英文缩写
D_PERIOD = {
    "本年迄今YTD": "ytd",
    "滚动季MQT": "mqt",
    "单月MON": "mon",
}

D_METRIC_MONTHLY = {
    "月度销售": "monthly_abs",
    "月度同比净增长": "monthly_diff",
    # "同比增长率": "gr",
    # "达成": "ach",
}


@login_required
def index(request):
    mselect_dict = {}
    for key, value in D_MULTI_SELECT.items():
        mselect_dict[key] = {}
        mselect_dict[key]["select"] = value
        mselect_dict[key]["options"] = get_distinct_list(value, DB_TABLE, ENGINE)

    context = {
        "date": DATE,
        "mselect_dict": mselect_dict,
        "period_dict": D_PERIOD,
        "monthly_metric_dict": D_METRIC_MONTHLY,
    }

    return render(request, "retail/display.html", context)


@login_required
def query(request):
    form_dict = qdict_to_dict(request.GET)
    print(form_dict)
    df = get_df(form_dict)
    print(df)
    # KPI字典
    kpi = get_kpi(df["销售"])

    # 是否只显示前200条结果，显示过多结果会导致前端渲染性能不足
    show_limit_results = form_dict["toggle_limit_show"]

    # 返回所选的分析维度
    dimension_select = form_dict["DIMENSION_select"]

    # # 综合表现指标汇总
    # ptable = format_table(
    #     get_ptable(
    #         df_sales=df["销售"], df_target=df["指标"], show_limit_results=show_limit_results
    #     ),
    #     "ptable",
    # )
    # ptable_comm = format_table(
    #     get_ptable_comm(
    #         df_sales=df["销售"],
    #         df_sales_comm=df["社区销售"],
    #         df_target_comm=df["社区指标"],
    #         show_limit_results=show_limit_results,
    #     ),
    #     "ptable_comm",
    # )

    # # 月度表现趋势表格
    # ptable_monthly = get_ptable_monthly(
    #     df_sales=df["销售"], show_limit_results=show_limit_results
    # )
    # ptable_comm_monthly = {}
    # temp = get_ptable_monthly(
    #     df_sales=df["社区销售"], show_limit_results=show_limit_results
    # )
    # for k, v in temp.items():
    #     ptable_comm_monthly[
    #         k.replace("ptable_monthly", "ptable_comm_monthly")
    #     ] = v.replace("ptable_monthly", "ptable_comm_monthly")

    # # 月度社区销售占比趋势
    # ptable_comm_ratio_monthly = format_table(
    #     get_ratio_monthly(
    #         df1=df["社区销售"],
    #         df2=df["销售"],
    #         table_name="社区销售占比趋势",
    #         show_limit_results=show_limit_results,
    #     ),
    #     "ptable_comm_ratio_monthly",
    # )

    # # 开户医院单产趋势
    # ptable_hppdt_monthly = format_table(
    #     get_ratio_monthly(
    #         df1=df["销售"],
    #         df2=df["开户医院数"],
    #         table_name="开户医院单产趋势",
    #         show_limit_results=show_limit_results,
    #     ),
    #     "ptable_hppdt_monthly",
    # )

    # # 代表单产趋势
    # ptable_rsppdt_monthly = format_table(
    #     get_ratio_monthly(
    #         df1=df["销售"],
    #         df2=df["代表数"],
    #         table_name="代表单产趋势",
    #         show_limit_results=show_limit_results,
    #     ),
    #     "ptable_rsppdt_monthly",
    # )

    # # Pyecharts交互图表
    # bar_total_monthly_trend = prepare_chart(
    #     df["销售"], df["指标"], "bar_total_monthly_trend", form_dict
    # )
    # scatter_sales_abs_diff = prepare_chart(
    #     df["销售"], df["指标"], "scatter_sales_abs_diff", form_dict
    # )
    # scatter_sales_comm_abs_diff = prepare_chart(
    #     df["社区销售"], df["社区指标"], "scatter_sales_abs_diff", form_dict
    # )
    # # pie_product = json.loads(prepare_chart(df_sales, df_target, "pie_product", form_dict))

    context = {
        "show_limit_results": show_limit_results,
        "dimension_select": dimension_select,
        # "ptable": ptable,
    }

    context = dict(context, **kpi)

    return HttpResponse(
        json.dumps(context, ensure_ascii=False),
        content_type="application/json charset=utf-8",
    )  # 返回结果必须是json格式


def get_df(form_dict, is_pivoted=True):
    sql = sqlparse(context=form_dict)  # sql拼接
    print(sql)
    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe
    print(df.columns)

    if is_pivoted is True:
        return {
            "销售": pivot(df=df, form_dict=form_dict),
            "客户数": pivot(df=df, form_dict=form_dict, type="count_client"),
            "代表数": pivot(df=df, form_dict=form_dict, type="count_rsp"),
        }

    else:
        return df


def sqlparse(context):
    sql = "Select * from %s WHERE 1=1" % DB_TABLE  # 先处理单选部分
    if context["customized_sql"] == "":
        # 如果前端没有输入自定义sql，直接循环处理多选部分进行sql拼接
        for k, v in context.items():
            if k not in [
                "csrfmiddlewaretoken",
                "DIMENSION_select",
                "PERIOD_select",
                "UNIT_select",
                "toggle_limit_show",
                "customized_sql",
            ]:
                if k[-2:] == "[]":
                    field_name = k[:-9]  # 如果键以[]结尾，删除_select[]取原字段名
                else:
                    field_name = k[:-7]  # 如果键不以[]结尾，删除_select取原字段名
                selected = v  # 选择项
                sql = sql_extent(sql, field_name, selected)  # 未来可以通过进一步拼接字符串动态扩展sql语句
    else:
        sql = context["customized_sql"]  # 如果前端输入了自定义sql，忽略前端其他参数直接处理
    return sql


def pivot(df, form_dict, type="sales"):
    column = form_dict["DIMENSION_select"]  # 分析维度
    unit_selected = form_dict["UNIT_select"]  # 单位（盒数、标准盒数、金额）

    if type == "sales":
        pivoted = pd.pivot_table(
            df,
            values=unit_selected,  # 数据透视汇总值为AMOUNT字段，一般保持不变
            index="DATE",  # 数据透视行为DATE字段，一般保持不变
            columns=column,  # 数据透视列为前端选择的分析维度
            aggfunc=np.sum,
        )  # 数据透视汇总方式为求和，一般保持不变
    elif type == "count_client":
        pivoted = pd.pivot_table(
            df,
            values="CLIENT_ID",  # 数据透视汇总值为HOSPITAL字段
            index="DATE",  # 数据透视行为DATE字段，一般保持不变
            columns=column,  # 数据透视列为前端选择的分析维度
            aggfunc=pd.Series.nunique,
        )  # 数据透视汇总方式为计数
    elif type == "count_rsp":
        pivoted = pd.pivot_table(
            df,
            values="RSP_ID",  # 数据透视汇总值为RSP字段
            index="DATE",  # 数据透视行为DATE字段，一般保持不变
            columns=column,  # 数据透视列为前端选择的分析维度
            aggfunc=pd.Series.nunique,
        )  # 数据透视汇总方式为计数

    if pivoted.empty is False:
        pivoted.sort_values(
            by=pivoted.index[-1], axis=1, ascending=False, inplace=True
        )  # 结果按照最后一个DATE表现排序
        pivoted.fillna(0, inplace=True)
        pivoted = pd.DataFrame(pivoted.to_records())
        pivoted.set_index("DATE", inplace=True)

    return pivoted


def get_kpi(df_sales: pd.DataFrame, df_target: pd.DataFrame = None) -> dict:
    kpi = {}

    for k, v in D_PERIOD.items():
        # 按列求和为查询总销售的Series
        sales_total = df_sales.sum(axis=1)

        if sales_total.empty is True:
            sales = 0
            sales_ya = 0
        else:
            # YTD销售
            sales = sales_total.loc[date_mask(df_sales, DATE, v)[0]].sum()
            # YTDYA销售
            sales_ya = sales_total.loc[date_mask(df_sales, DATE, v)[1]].sum()
        try:
            # YTD同比增长
            sales_gr = sales / sales_ya - 1
        except ZeroDivisionError:
            sales_gr = np.inf

        # 按列求和为查询总指标的Series
        if df_target is not None:
            target_total = df_target.sum(axis=1)
            if target_total.empty is True:
                target = 0
            else:
                # YTD指标
                target = target_total.loc[date_mask(df_target, DATE, v)[0]].sum()
            try:
                # YTD达标率
                ach = sales / target
            except ZeroDivisionError:
                ach = np.inf
        else:
            target = "N/A"
            ach = "N/A"

        if sales_gr == np.inf or sales_gr == -np.inf:
            sales_gr = "N/A"
        if ach == np.inf or ach == -np.inf:
            ach = "N/A"

        kpi = dict(
            kpi,
            **{
                "sales_%s" % v: int(sales),
                "sales_gr_%s" % v: sales_gr,
                "target_%s" % v: int(target),
                "ach_%s" % v: ach,
            }
        )

    return kpi
