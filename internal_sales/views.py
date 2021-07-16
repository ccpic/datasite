from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from sqlalchemy import create_engine
import pandas as pd
import json
import numpy as np
from .models import *
import six
import datetime
from dateutil.relativedelta import relativedelta
from chpa_data.charts import *

try:
    from io import BytesIO as IO  # for modern python
except ImportError:
    from io import StringIO as IO  # for legacy python

ENGINE = create_engine("mssql+pymssql://(local)/Internal_sales")  # 创建数据库连接引擎
DB_TABLE = "data"
date = datetime.datetime(year=2021, month=6, day=1) # 目标分析月份
date_ya = date.replace(year=date.year - 1)  # 同比月份
date_year_begin = date.replace(month=1)  # 本年度开头
date_ya_begin = date_ya.replace(month=1)  # 去年开头
PRODUCTS_HAVE_TARGET = ["信立坦", "欣复泰"]  # 有指标的产品

# 该字典为数据库字段名和Django Model的关联
D_MODEL = {
    "PROVINCE": Province,
    "CITY": City,
    "COUNTY": County,
    "HOSPITAL": Hospital,
    "LEVEL": Level,
    "PRODUCT": Product,
    "BU": BU,
    "RD": RD,
    "RM": RM_POS_NAME,
    "DSM": DSM_POS_NAME,
    "RSP": RSP_POS_NAME,
}


# 该字典key为前端准备显示的所有多选字段名, value为数据库对应的字段名
D_MULTI_SELECT = {
    "产品": "PRODUCT",
    "省份": "PROVINCE",
    "城市": "CITY",
    "区县": "COUNTY",
    "医院等级": "LEVEL",
    "医院": "HOSPITAL",
    "南北中国": "BU",
    "区域": "RD",
    "大区经理": "RM_POS_NAME",
    "地区经理": "DSM_POS_NAME",
    "代表": "RSP_POS_NAME",
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
        mselect_dict[key]["options"] = get_distinct_list(value, DB_TABLE)

    context = {
        "date": date,
        "mselect_dict": mselect_dict,
        "period_dict": D_PERIOD,
        "monthly_metric_dict": D_METRIC_MONTHLY,
    }

    return render(request, "internal_sales/display.html", context)


def get_distinct_list(column, db_table):
    sql = "Select DISTINCT " + column + " From " + db_table
    df = pd.read_sql_query(sql, ENGINE)
    df.dropna(inplace=True)
    l = df.values.flatten().tolist()
    return l


@login_required
def query(request):
    form_dict = dict(six.iterlists(request.GET))
    df = get_df(form_dict)

    # KPI字典
    kpi = get_kpi(df["销售"], df["带指标销售"], df["指标"])

    # 是否只显示前200条结果，显示过多结果会导致前端渲染性能不足
    show_limit_results = form_dict["toggle_limit_show"][0]

    # 综合表现指标汇总
    ptable = format_table(
        get_ptable(
            df_sales=df["销售"], df_target=df["指标"], show_limit_results=show_limit_results
        ),
        "ptable",
    )
    ptable_comm = format_table(
        get_ptable_comm(
            df_sales=df["销售"],
            df_sales_comm=df["社区销售"],
            df_target_comm=df["社区指标"],
            show_limit_results=show_limit_results,
        ),
        "ptable_comm",
    )

    # 月度表现趋势表格
    ptable_monthly = get_ptable_monthly(
        df_sales=df["销售"], show_limit_results=show_limit_results
    )
    ptable_comm_monthly = {}
    temp = get_ptable_monthly(
        df_sales=df["社区销售"], show_limit_results=show_limit_results
    )
    for k, v in temp.items():
        ptable_comm_monthly[
            k.replace("ptable_monthly", "ptable_comm_monthly")
        ] = v.replace("ptable_monthly", "ptable_comm_monthly")

    # 月度社区销售占比趋势
    ptable_comm_ratio_monthly = format_table(
        get_ratio_monthly(
            df1=df["社区销售"],
            df2=df["销售"],
            table_name="社区销售占比趋势",
            show_limit_results=show_limit_results,
        ),
        "ptable_comm_ratio_monthly",
    )

    # 开户医院单产趋势
    ptable_hppdt_monthly = format_table(
        get_ratio_monthly(
            df1=df["销售"],
            df2=df["开户医院数"],
            table_name="开户医院单产趋势",
            show_limit_results=show_limit_results,
        ),
        "ptable_hppdt_monthly",
    )

    # 代表单产趋势
    ptable_rsppdt_monthly = format_table(
        get_ratio_monthly(
            df1=df["销售"],
            df2=df["代表数"],
            table_name="代表单产趋势",
            show_limit_results=show_limit_results,
        ),
        "ptable_rsppdt_monthly",
    )

    # Pyecharts交互图表
    bar_total_monthly_trend = prepare_chart(
        df["销售"], df["指标"], "bar_total_monthly_trend", form_dict
    )
    scatter_sales_abs_diff = prepare_chart(
        df["销售"], df["指标"], "scatter_sales_abs_diff", form_dict
    )
    scatter_sales_comm_abs_diff = prepare_chart(
        df["社区销售"], df["社区指标"], "scatter_sales_abs_diff", form_dict
    )
    # pie_product = json.loads(prepare_chart(df_sales, df_target, "pie_product", form_dict))

    context = {
        "show_limit_results": show_limit_results,
        "ptable": ptable,
        "ptable_comm": ptable_comm,
        "ptable_comm_ratio_monthly": ptable_comm_ratio_monthly,
        "ptable_hppdt_monthly": ptable_hppdt_monthly,
        "ptable_rsppdt_monthly": ptable_rsppdt_monthly,
        "bar_total_monthly_trend": bar_total_monthly_trend,
        "scatter_sales_abs_diff": scatter_sales_abs_diff,
        "scatter_sales_comm_abs_diff": scatter_sales_comm_abs_diff,
        # "pie_product": pie_product,
    }

    context = dict(context, **kpi)
    context = dict(context, **ptable_monthly)
    context = dict(context, **ptable_comm_monthly)

    return HttpResponse(
        json.dumps(context, ensure_ascii=False),
        content_type="application/json charset=utf-8",
    )  # 返回结果必须是json格式


@login_required
def export(request, type):
    form_dict = dict(six.iterlists(request.GET))

    excel_file = IO()
    xlwriter = pd.ExcelWriter(excel_file, engine="xlsxwriter")

    if type == "pivoted":
        df = get_df(form_dict)  # 透视后的数据
        for key, value in df.items():
            value.to_excel(xlwriter, sheet_name=key, index=True)
    elif type == "raw":
        df = get_df(form_dict, is_pivoted=False)  # 原始数
        df.to_excel(xlwriter, sheet_name="data", index=False)

    xlwriter.save()
    xlwriter.close()

    excel_file.seek(0)

    # 设置浏览器mime类型
    response = HttpResponse(
        excel_file.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # 设置文件名
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 当前精确时间不会重复，适合用来命名默认导出文件
    response["Content-Disposition"] = "attachment; filename=" + now + ".xlsx"
    return response


def get_ptable(df_sales, df_target, show_limit_results):  # 销售指标汇总
    if df_sales.empty is False:
        df_combined = calculate_sales_metric(df_sales, df_target)
    else:
        df_combined = pd.DataFrame(columns=["指标汇总"])

    if show_limit_results == "true":
        df_combined = df_combined.iloc[:200, :]

    return df_combined


def get_ratio_monthly(
    df1, df2, table_name, show_limit_results
):  # 用以计算医院单产，代表单产，社区占比等ratio指标
    if df1.empty is False:
        if df2.empty is False:
            mask1 = date_mask(df1, "mat")[0]
            mask2 = date_mask(df2, "mat")[0]
            df = df1.loc[mask1, :] / df2.loc[mask2, :]
            df.dropna(how="all", axis=1, inplace=True)
            df.fillna(0, inplace=True)
            df = df.T
            df.columns = df.columns.strftime("%Y-%m")
            df.sort_values(by=df.columns.tolist()[-1], ascending=False, inplace=True)

            if show_limit_results == "true":
                df = df.iloc[:200, :]

            df["趋势"] = None  # 表格最右侧预留Sparkline空列
        else:
            df = pd.DataFrame(columns=[table_name])
    else:
        df = pd.DataFrame(columns=[table_name])
    return df


def get_ptable_monthly(df_sales, show_limit_results):  # 月度明细
    if df_sales.empty is False:
        mask = date_mask(df_sales, "mat")[0]
        df_sales_abs = df_sales.loc[mask, :].T
        if show_limit_results == "true":
            df_sales_abs = df_sales_abs.iloc[:200, :]
        df_sales_abs.columns = df_sales_abs.columns.strftime("%Y-%m")
        df_sales_abs["趋势"] = None  # 表格最右侧预留Sparkline空列

        df_sales_diff = df_sales.diff(periods=12).loc[mask, :].T
        if show_limit_results == "true":
            df_sales_diff = df_sales_diff.iloc[:200, :]
        df_sales_diff.columns = df_sales_diff.columns.strftime("%Y-%m")
        df_sales_diff["趋势"] = None
        d = {
            "ptable_monthly_abs": format_table(df_sales_abs, "ptable_monthly_abs"),
            "ptable_monthly_diff": format_table(df_sales_diff, "ptable_monthly_diff"),
        }
    else:
        d = {
            "ptable_monthly_abs": format_table(
                pd.DataFrame(columns=["月度明细"]), "ptable_monthly_abs"
            ),
            "ptable_monthly_diff": format_table(
                pd.DataFrame(columns=["月度明细"]), "ptable_monthly_diff"
            ),
        }
    return d


def get_ptable_comm(
    df_sales, df_sales_comm, df_target_comm, show_limit_results
):  # 社区表现
    if df_sales.empty is False:
        mask_ytd = date_mask(df_sales, "ytd")[0]  # ytd时间段销售
        df_sales_ytd = df_sales.loc[mask_ytd, :].sum(axis=0)
        mask_ytdya = date_mask(df_sales, "ytd")[1]  # ytd同比时间段销售
        df_sales_ytdya = df_sales.loc[mask_ytdya, :].sum(axis=0)

        if df_sales_comm.empty is False:
            df_combined = calculate_sales_metric(df_sales_comm, df_target_comm)
            df_combined.columns = "社区" + df_combined.columns

            mask_ytd = date_mask(df_sales_comm, "ytd")[0]  # ytd时间段销售
            df_sales_comm_ytd = df_sales_comm.loc[mask_ytd, :].sum(axis=0)
            df_sales_comm_contrib_ytd = df_sales_comm_ytd / df_sales_ytd  # ytd时间段自身社区占比

            mask_ytdya = date_mask(df_sales_comm, "ytd")[1]  # ytd同比时间段销售
            df_sales_comm_ytdya = df_sales_comm.loc[mask_ytdya, :].sum(axis=0)
            df_sales_comm_contrib_ytdya = (
                df_sales_comm_ytdya / df_sales_ytdya
            )  # ytd同比时间段自身社区占比
            df_sales_comm_contrib_diff_ytd = (
                df_sales_comm_contrib_ytd - df_sales_comm_contrib_ytdya
            )

            df_combined = pd.concat(
                [
                    df_combined,
                    df_sales_comm_contrib_ytd,
                    df_sales_comm_contrib_diff_ytd,
                ],
                axis=1,
            )
            df_combined.rename(columns={0: "自身社区占比", 1: "社区占比同比变化"}, inplace=True)
            df_combined.fillna(
                {
                    "社区销售": 0,
                    "社区销售贡献份额": 0,
                    "社区同比净增长": 0,
                    "社区销售贡献份额同比变化": 0,
                    "自身社区占比": 0,
                    "社区占比同比变化": 0,
                },
                inplace=True,
            )
            df_combined.sort_values(by="社区销售", axis=0, ascending=False, inplace=True)

            if show_limit_results == "true":
                df_combined = df_combined.iloc[:200, :]
        else:
            df_combined = pd.DataFrame(columns=["社区表现"])

    else:
        df_combined = pd.DataFrame(columns=["社区表现"])

    return df_combined


def calculate_sales_metric(df_sales, df_target):
    mask_ytd = date_mask(df_sales, "ytd")[0]  # ytd时间段销售
    df_sales_ytd = df_sales.loc[mask_ytd, :].sum(axis=0)
    df_sales_share_ytd = df_sales_ytd.div(df_sales_ytd.sum())

    mask_ytdya = date_mask(df_sales, "ytd")[1]  # ytd同比时间段销售
    df_sales_ytdya = df_sales.loc[mask_ytdya, :].sum(axis=0)
    df_sales_share_ytdya = df_sales_ytdya.div(df_sales_ytdya.sum())

    df_sales_diff_ytd = df_sales_ytd - df_sales_ytdya  # ytd净增长
    df_sales_share_diff_ytd = df_sales_share_ytd - df_sales_share_ytdya  # ytd份额变化
    df_sales_gr_ytd = df_sales_ytd / df_sales_ytdya - 1  # ytd增长率

    # mask_qtr = date_mask(df_sales, "qtr")[0]
    # mask_qtrqa = date_mask(df_sales, "qtr")[1]
    #
    # df_sales_qtr = df_sales.loc[mask_qtr, :].mean(axis=0)  # 当季平均
    # df_sales_qtrqa = df_sales.loc[mask_qtrqa, :].mean(axis=0)  # 上季平均
    # df_sales_gr_qa = df_sales_qtr / df_sales_qtrqa - 1  # 季平均环比

    mask_mqt = date_mask(df_sales, "mqt")[0]
    mask_mqtqa = (df_sales.index >= date + relativedelta(months=-5)) & (
        df_sales.index <= date + relativedelta(months=-3)
    )

    df_sales_mqt = df_sales.loc[mask_mqt, :].sum(axis=0)  # 滚动季销售
    df_sales_mqtqa = df_sales.loc[mask_mqtqa, :].sum(axis=0)  # 滚动季环比销售

    df_sales_gr_qa = df_sales_mqt / df_sales_mqtqa - 1  # 滚动季环比增长率

    if df_target.empty is False:
        mask_ytd = date_mask(df_target, "ytd")[0]
        df_target_ytd = df_target.loc[mask_ytd, :].sum(axis=0)  # YTD指标
        df_ach_ytd = df_sales_ytd / df_target_ytd  # YTD达成
    else:
        df_target_ytd = pd.Series(np.nan, index=df_sales_ytd.index)
        df_ach_ytd = pd.Series(np.nan, index=df_sales_ytd.index)

    df_combined = pd.concat(
        [
            df_sales_ytd,
            df_sales_share_ytd,
            df_sales_diff_ytd,
            df_sales_share_diff_ytd,
            df_sales_gr_ytd,
            df_sales_gr_qa,
            df_target_ytd,
            df_ach_ytd,
        ],
        axis=1,
    )

    df_combined.columns = [
        "销售",
        "销售贡献份额",
        "同比净增长",
        "销售贡献份额同比变化",
        "同比增长率",
        "滚动季环比增长率",
        "指标",
        "同期达成",
    ]
    df_combined.fillna(
        {"销售": 0, "销售贡献份额": 0, "同比净增长": 0, "销售贡献份额同比变化": 0}, inplace=True
    )
    df_combined.sort_values(by="销售", axis=0, ascending=False, inplace=True)

    return df_combined


def get_kpi(df_sales, df_sales_tpo, df_target):
    kpi = {}

    for k, v in D_PERIOD.items():
        # 按列求和为查询总销售的Series
        sales_total = df_sales.sum(axis=1)

        if sales_total.empty is True:
            sales = 0
            sales_ya = 0
        else:
            # YTD销售
            sales = sales_total.loc[date_mask(df_sales, v)[0]].sum()
            # YTDYA销售
            sales_ya = sales_total.loc[date_mask(df_sales, v)[1]].sum()
        try:
            # YTD同比增长
            sales_gr = sales / sales_ya - 1
        except ZeroDivisionError:
            sales_gr = np.inf

        sales_total_tpo = df_sales_tpo.sum(axis=1)
        if sales_total_tpo.empty is True:
            sales_tpo = 0
        else:
            sales_tpo = sales_total_tpo.loc[date_mask(df_sales_tpo, v)[0]].sum()
        # 按列求和为查询总指标的Series
        target_total = df_target.sum(axis=1)
        if target_total.empty is True:
            target = 0
        else:
            # YTD指标
            target = target_total.loc[date_mask(df_target, v)[0]].sum()
        try:
            # YTD达标率
            ach = sales_tpo / target
        except ZeroDivisionError:
            ach = np.inf

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


def format_table(df, id):
    formatters = build_formatters_by_col(df=df, table_id=id)

    table_formatted = df.to_html(
        escape=False,
        formatters=formatters,  # 逐列调整表格内数字格式
        classes="ui selectable celled table",  # 指定表格css class为Semantic UI主题
        table_id=id,  # 指定表格id
    )
    return table_formatted


def date_mask(df, period):
    if period == "ytd":
        mask = (df.index >= date_year_begin) & (df.index <= date)
        mask_ya = (df.index >= date_ya_begin) & (df.index <= date_ya)
    elif period == "mat":
        mask = (df.index >= date + relativedelta(months=-11)) & (df.index <= date)
        mask_ya = (df.index >= date_ya + relativedelta(months=-11)) & (
            df.index <= date_ya
        )
    elif period == "mqt":
        mask = (df.index >= date + relativedelta(months=-2)) & (df.index <= date)
        mask_ya = (df.index >= date_ya + relativedelta(months=-2)) & (
            df.index <= date_ya
        )
    elif period == "mon":
        mask = df.index == date
        mask_ya = df.index == date_ya
    elif period == "qtr":  # 返回当季和环比季度的mask，当季可能不是一个完整季，环比季度是一个完整季
        month = date.month
        first_month_in_qtr = (month - 1) // 3 * 3 + 1  # 找到本季度的第一个月
        date_first_month_in_qtr = date.replace(month=first_month_in_qtr)
        date_first_month_in_qtrqa = date_first_month_in_qtr + relativedelta(months=-3)
        date_last_month_in_qtrqa = date_first_month_in_qtr + relativedelta(months=-1)
        mask = (df.index >= date_first_month_in_qtr) & (df.index <= date)
        mask_ya = (df.index >= date_first_month_in_qtrqa) & (
            df.index <= date_last_month_in_qtrqa
        )

    return mask, mask_ya


def get_df(form_dict, is_pivoted=True):
    sql = sqlparse(form_dict)  # sql拼接
    print(sql)
    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe

    df["HOSPITAL"] = df["HOSPITAL"].str[11:]  # 因医院全名太长，去除医院10位编码

    if is_pivoted is True:
        return {
            "销售": pivot(df=df[df.TAG != "指标"], form_dict=form_dict),
            "社区销售": pivot(
                df=df[(df.TAG != "指标") & (df.LEVEL.isin(["旗舰社区", "普通社区"]))],
                form_dict=form_dict,
            ),
            "带指标销售": pivot(
                df=df[(df.TAG != "指标") & (df.PRODUCT.isin(PRODUCTS_HAVE_TARGET))],
                form_dict=form_dict,
            ),
            "指标": pivot(
                df=df[(df.TAG == "指标") & (df.PRODUCT.isin(PRODUCTS_HAVE_TARGET))],
                form_dict=form_dict,
            ),
            "社区指标": pivot(
                df=df[(df.TAG == "指标") & (df.LEVEL.isin(["旗舰社区", "普通社区"]))],
                form_dict=form_dict,
            ),
            "开户医院数": pivot(df=df[df.TAG != "指标"], form_dict=form_dict, type="count_hp"),
            "代表数": pivot(df=df[df.TAG != "指标"], form_dict=form_dict, type="count_rsp"),
        }

    else:
        return df


def pivot(df, form_dict, type="sales"):
    dimension_selected = form_dict["DIMENSION_select"][0]  # 分析维度
    unit_selected = form_dict["UNIT_select"][0]  # 单位（盒数、标准盒数、金额）
    if dimension_selected[0] == "[":
        column = dimension_selected[1:][:-1]
    else:
        column = dimension_selected

    if type == "sales":
        pivoted = pd.pivot_table(
            df,
            values=unit_selected,  # 数据透视汇总值为AMOUNT字段，一般保持不变
            index="DATE",  # 数据透视行为DATE字段，一般保持不变
            columns=column,  # 数据透视列为前端选择的分析维度
            aggfunc=np.sum,
        )  # 数据透视汇总方式为求和，一般保持不变
    elif type == "count_hp":
        pivoted = pd.pivot_table(
            df,
            values="HP_ID",  # 数据透视汇总值为HOSPITAL字段
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


@login_required
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
        json.dumps(res, ensure_ascii=False),
        content_type="application/json charset=utf-8",
    )  # 返回结果必须是json格式


def build_formatters_by_col(df, table_id):
    format_abs = lambda x: "{:,.0f}".format(x)
    format_share = lambda x: "{:.1%}".format(x)
    format_gr = lambda x: "{:+.1%}".format(x)
    format_currency = lambda x: "¥{:,.1f}".format(x)

    d = {}
    if table_id == "ptable_comm_ratio_monthly":
        for column in df.columns:
            d[column] = format_share
    else:
        for column in df.columns:
            if (
                "同比增长" in str(column)
                or "增长率" in str(column)
                or "CAGR" in str(column)
                or "同比变化" in str(column)
            ):
                d[column] = format_gr
            elif (
                "份额" in str(column)
                or "贡献" in str(column)
                or "达成" in str(column)
                or "占比" in str(column)
            ):
                d[column] = format_share
            elif "价格" in str(column) or "单价" in str(column):
                d[column] = format_currency
            elif "趋势" in str(column):
                d[column] = None
            else:
                d[column] = format_abs

    return d


def prepare_chart(
    df_sales,  # 销售数据df, 输入经过pivoted方法透视过的df，不是原始df
    df_target,  # 指标数据df
    chart_type,  # 图表类型字符串，人为设置，根据图表类型不同做不同的Pandas数据处理，及生成不同的Pyechart对象
    form_dict,  # 前端表单字典，用来获得一些变量作为图表的标签如单位
):
    SERIES_LIMIT = 10  # 折线图等系列限制
    show_limit_results = form_dict["toggle_limit_show"][
        0
    ]  # 散点图等是否只显示前200条结果，显示过多结果会导致前端渲染性能不足
    # label = D_TRANS[form_dict["PERIOD_select"][0]] + D_TRANS[form_dict["UNIT_select"][0]]
    if df_sales.empty is False:
        if chart_type == "bar_total_monthly_trend":
            form_dict_by_product = form_dict.copy()
            form_dict_by_product["DIMENSION_select"] = [
                "PRODUCT"
            ]  # 前端控件交互字典将分析维度替换成PRODUCT

            df_sales_by_product = get_df(form_dict_by_product)["销售"].astype("int")
            df_sales_by_product.index = df_sales_by_product.index.strftime(
                "%Y-%m"
            )  # 行索引日期数据变成2020-06的形式
            # df_target_total = df_target.sum(axis=1)[:-1]  # 获取目标总和
            # df_target_total.index = df_target_total.index.strftime("%Y-%m")
            # df_ach_total = df_sales_total/df_target_total
            # df_ach_total.replace([np.inf, -np.inf, np.nan], "-", inplace=True)  # 所有分母为0或其他情况导致的inf和nan都转换为'-'
            #
            # df_sales_total = df_sales_total.to_frame()  # series转换成df
            # df_sales_total.columns = ['月度销售']
            # df_ach_total = df_ach_total.to_frame() # series转换成df
            # df_ach_total.columns = ['指标达成率']

            chart = echarts_stackbar(
                df=df_sales_by_product
            )  # 调用stackbar方法生成Pyecharts图表对象

            return json.loads(chart.dump_options())  # 用json格式返回Pyecharts图表对象的全局设置
        elif chart_type == "pie_product":
            form_dict_by_product = form_dict.copy()
            form_dict_by_product["DIMENSION_select"] = [
                "PRODUCT"
            ]  # 前端控件交互字典将分析维度替换成PRODUCT
            df_by_product = get_df(form_dict_by_product)["销售"]

            mask = date_mask(df_by_product, "ytd")[0]
            df_by_product_ytd = df_by_product.loc[mask, :]
            df_by_product_ytd = df_by_product_ytd.sum(axis=0)
            # df_count = df['客户姓名'].groupby(df['所在科室']).count()
            # df_count = df_count.reindex(['心内科', '肾内科', '神内科', '内分泌科', '老干科', '其他科室'])
            chart = pie_radius(df_by_product_ytd)

            return json.loads(chart.dump_options())  # 用json格式返回Pyecharts图表对象的全局设置
        elif chart_type == "scatter_sales_abs_diff":
            metrics = calculate_sales_metric(df_sales, df_target)

            if show_limit_results == "true":
                metrics = metrics.iloc[:200, :]

            chart = echarts_scatter(metrics[["销售", "同比净增长"]])

            return json.loads(chart.dump_options())
        else:
            return json.dumps(None)
    else:
        return json.dumps(None)
    # elif chart_type == "stackarea_abs_trend":
    #     chart = echarts_stackarea(df.iloc[:, :SERIES_LIMIT], datatype="ABS")  # 直接使用绝对值时间序列
    #     return chart.dump_options()
    # elif chart_type == "stackarea_share_trend":
    #     df_share = df.transform(lambda x: x / x.sum(), axis=1)  # 时间序列转换为份额趋势
    #     df_share.replace([np.inf, -np.inf, np.nan], "-", inplace=True)  # 替换缺失值
    #     chart = echarts_stackarea100(df_share.iloc[:, :SERIES_LIMIT], datatype="SHARE")
    #     return chart.dump_options()
    # elif chart_type == "line_gr_trend":
    #     df_gr = df.pct_change(periods=4)  # 以4（同比）为间隔计算百分比增长
    #     df_gr.dropna(how="all", inplace=True)  # 删除因为没有分母而计算后变成na的前几个时序
    #     df_gr.replace([np.inf, -np.inf, np.nan], "-", inplace=True)  # 替换正负无穷
    #     chart = echarts_line(df_gr.iloc[:, :SERIES_LIMIT], datatype="GR")
    #     return chart.dump_options()
    # elif chart_type == "bubble_performance":
    #     df_abs = df.iloc[-1, :]  # 获取最新时间粒度的绝对值
    #     df_share = df.transform(lambda x: x / x.sum(), axis=1).iloc[-1, :]  # 获取份额
    #     df_diff = df.diff(periods=4).iloc[-1, :]  # 获取同比净增长
    #
    #     chart = mpl_bubble(
    #         x=df_abs,  # x轴数据
    #         y=df_diff,  # y轴数据
    #         z=df_share * 50000,  # 气泡大小数据
    #         labels=df.columns.str.split("|").str[0],  # 标签数据
    #         title="",  # 图表标题
    #         x_title=label,  # x轴标题
    #         y_title=label + "净增长",  # y轴标题
    #         x_fmt="{:,.0f}",  # x轴格式
    #         y_fmt="{:,.0f}",  # y轴格式
    #         y_avg_line=True,  # 添加y轴分隔线
    #         y_avg_value=0,  # y轴分隔线为y=0
    #         label_limit=30,  # 只显示前30个项目的标签
    #     )
    #     return chart
    # elif chart_type == "treemap_share":
    #     # 后续Squarify计算矩形面积不支持数据为0，要先去除pandas df最后一行为0的列
    #     mask = df.iloc[-1].index[df.iloc[-1] != 0]
    #     df2 = df[mask]
    #
    #     df_abs = df2.iloc[-1, :]  # 获取最新周期绝对值
    #     df_diff = df2.diff(periods=4).iloc[-1, :]  # 获取同比净增长，环比可以把4改成1
    #
    #     # 合并名称和值为Labels
    #     list_index = df_abs.index.tolist()
    #     list_name = []
    #     for name in list_index:
    #         if len(name) > 8:

    #             name = name[:8] + "..."  # 防止太长的标签，在之后的可视化中会出界
    #         list_name.append(name)
    #     list_value = df_abs.tolist()
    #     list_diff = df_diff.tolist()
    #     list_labels = [
    #         m + "\n" + str("{:,.0f}".format(n)) + "\n" + str("{:+,.0f}".format(p))
    #         for m, n, p in zip(list_name, list_value, list_diff)
    #     ]
    #
    #     chart = treemap(sizes=list_value, diff=list_diff, labels=list_labels, width=2, height=1)
    #     return chart
