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
from datasite.commons import format_table, get_distinct_list, sql_extent
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

try:
    from io import BytesIO as IO  # for modern python
except ImportError:
    from io import StringIO as IO  # for legacy python


ENGINE = create_engine("mssql+pymssql://(local)/Internal_sales")  # 创建数据库连接引擎
DB_TABLE = "potential"
SALES_VOL = "MAT202107"
PRODUCTS_HAVE_TARGET = ["信立坦", "欣复泰"]

# 该字典key为前端准备显示的所有多选字段名, value为数据库对应的字段名
D_MULTI_SELECT = {
    "医院类型": "HP_TYPE",
    "省份": "PROVINCE",
    "城市": "CITY",
    "区县": "COUNTY",
    "潜力分位（等级、社区各自内部）": "DECILE",
    "潜力分位（合并计算）": "DECILE_TOTAL",
    "医院": "HOSPITAL",
}


@login_required
def index(request):
    mselect_dict = {}
    for key, value in D_MULTI_SELECT.items():
        mselect_dict[key] = {}
        mselect_dict[key]["select"] = value
        mselect_dict[key]["options"] = get_distinct_list(value, DB_TABLE, ENGINE)

    context = {
        "date": SALES_VOL,
        "mselect_dict": mselect_dict,
    }

    return render(request, "potential/display.html", context)


@login_required
def query(request):
    form_dict = dict(six.iterlists(request.GET))
    df = get_df(form_dict)
    df = df.head(500)

    context = {"ptable": format_table(df=df, id="ptable")}

    # dimension_selected = form_dict["DIMENSION_select"][0]  # 分析维度

    # # 潜力部分
    # pivoted_potential = pd.pivot_table(
    #     data=df,
    #     values="POTENTIAL_DOT",
    #     index=dimension_selected,
    #     columns=None,
    #     aggfunc=[len, sum],
    #     fill_value=0,
    # )

    # pivoted_potential = pd.DataFrame(
    #     pivoted_potential.to_records()
    # )  # pivot table对象转为默认df
    # pivoted_potential.set_index(dimension_selected, inplace=True)
    # # pivoted_potential.reset_index(axis=1, inplace=True)
    # pivoted_potential.columns = ["终端数量", "潜力(DOT)"]
    # pivoted_potential["潜力贡献"] = (
    #     pivoted_potential["潜力(DOT)"] / pivoted_potential["潜力(DOT)"].sum()
    # )

    # # 覆盖部分
    # pivoted_access = pd.pivot_table(
    #     data=df,
    #     values="POTENTIAL_DOT",
    #     index=dimension_selected,
    #     columns="SALES_COND",
    #     aggfunc=[len, sum],
    #     fill_value=0,
    # )
    # pivoted_access = pd.DataFrame(pivoted_access.to_records())  # pivot table对象转为默认df
    # pivoted_access.set_index(dimension_selected, inplace=True)
    # # pivoted_access.reset_index(axis=1, inplace=True)
    # pivoted_access.columns = [
    #     "无销量目标医院终端数量",
    #     "有销量目标医院终端数量",
    #     "非目标医院终端数量",
    #     "无销量目标医院潜力(DOT)",
    #     "有销量目标医院潜力(DOT)",
    #     "非目标医院潜力(DOT)",
    # ]
    # pivoted_access["信立坦目标覆盖终端数量"] = (
    #     pivoted_access["无销量目标医院终端数量"] + pivoted_access["有销量目标医院终端数量"]
    # )
    # pivoted_access["信立坦目标覆盖潜力(DOT)"] = (
    #     pivoted_access["有销量目标医院潜力(DOT)"] + pivoted_access["无销量目标医院潜力(DOT)"]
    # )
    # pivoted_access["信立坦目标覆盖潜力(DOT %)"] = pivoted_access[
    #     "信立坦目标覆盖潜力(DOT)"
    # ] / pivoted_access.sum(axis=1)
    # pivoted_access["信立坦销售覆盖终端数量"] = pivoted_access["有销量目标医院终端数量"]
    # pivoted_access["信立坦销售覆盖潜力(DOT %)"] = pivoted_access[
    #     "有销量目标医院潜力(DOT)"
    # ] / pivoted_access.sum(axis=1)

    # # 内部销售部分
    # pivoted_sales = pd.pivot_table(
    #     data=df,
    #     values="SALES_MAT",
    #     index=dimension_selected,
    #     columns=None,
    #     aggfunc=sum,
    #     fill_value=0,
    # )
    # pivoted_sales = pd.DataFrame(
    #     pivoted_sales.to_records()
    # )  # pivot table对象转为默认df
    # pivoted_sales.set_index(dimension_selected, inplace=True)
    # pivoted_sales.columns = ["信立坦MAT销量(DOT)"]
    # pivoted_sales["信立坦销售贡献"] = (
    #     pivoted_sales["信立坦MAT销量(DOT)"] / pivoted_sales["信立坦MAT销量(DOT)"].sum()
    # )

    # kpi = {
    #     "潜力汇总(DOT)": int(pivoted_potential["潜力(DOT)"].sum()),
    #     "有潜力值的终端数量": int(pivoted_potential["终端数量"].sum()),
    #     "信立坦目标终端覆盖潜力(DOT %)": pivoted_access["信立坦目标覆盖潜力(DOT)"].sum()
    #     / pivoted_potential["潜力(DOT)"].sum(),
    #     "信立坦目标终端数量": int(pivoted_access["信立坦目标覆盖终端数量"].sum()),
    #     "信立坦有量终端覆盖潜力(DOT %)": pivoted_access["有销量目标医院潜力(DOT)"].sum()
    #     / pivoted_potential["潜力(DOT)"].sum(),
    #     "信立坦有量终端数量": int(pivoted_access["信立坦销售覆盖终端数量"].sum()),
    #     "信立坦所有终端份额": pivoted_sales["信立坦MAT销量(DOT)"].sum()/pivoted_potential["潜力(DOT)"].sum(),
    #     "信立坦目标终端份额": pivoted_sales["信立坦MAT销量(DOT)"].sum()/pivoted_access["信立坦目标覆盖潜力(DOT)"].sum(),
    #     "信立坦有量终端份额": pivoted_sales["信立坦MAT销量(DOT)"].sum()/pivoted_access["有销量目标医院潜力(DOT)"].sum(),
    # }

    # # 是否只显示前200条结果，显示过多结果会导致前端渲染性能不足
    # show_limit_results = form_dict["toggle_limit_show"][0]

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
    # pie_product = json.loads(prepare_chart(df_sales, df_target, "pie_product", form_dict))

    # context = {}

    # context = dict(context, **kpi)
    # context = dict(context, **ptable_monthly)
    # context = dict(context, **ptable_comm_monthly)

    return HttpResponse(
        json.dumps(context, ensure_ascii=False),
        content_type="application/json charset=utf-8",
    )  # 返回结果必须是json格式


@login_required()
def table_hp(request):
    print(request.POST)
    form_dict = json.loads(request.POST.get("formdata")) # filter栏表单数据
    df = get_df(form_dict)
    
    # 查询常数设置
    ORDER_DICT = {
        0: "bu",
        # 1: "rd",
        1: "rm",
        2: "dsm",
        3: "rsp",
        4: "hospital",
        5: "hp_level",
        6: "name",
        7: "dept",
        8: "title",
        9: "consulting_times",
        10: "patients_half_day",
        11: "target_prop",
        12: "note",
        13: "monthly_target_patients",
        14: "potential_level",
    }

    dataTable = {}
    aodata = json.loads(request.POST.get("aodata"))

    for item in aodata:
        if item["name"] == "sEcho":
            sEcho = int(item["value"])  # 客户端发送的标识
        if item["name"] == "iDisplayStart":
            start = int(item["value"])  # 起始索引
        if item["name"] == "iDisplayLength":
            length = int(item["value"])  # 每页显示的行数
        if item["name"] == "iSortCol_0":
            sort_column = int(item["value"])  # 按第几列排序
        if item["name"] == "sSortDir_0":
            sort_order = item["value"].lower()  # 正序还是反序
        if item["name"] == "sSearch":
            search_key = item["value"]  # 搜索关键字

    # # 根据前端返回筛选参数筛选
    # context = get_context_from_form(request)

    # # 根据用户权限，前端参数，搜索关键字返回client objects
    # # user_auth = ast.literal_eval(request.POST.get("user_auth"))
    # clients = get_clients(user_auth, context, search_key)

    # # 排序
    # result_length = clients.count()
    # if sort_column < 43:
    #     if sort_order == "asc":
    #         clients = sorted(
    #             clients, key=lambda a: getattr(a, ORDER_DICT[sort_column])
    #         )
    #     elif sort_order == "desc":
    #         clients = sorted(
    #             clients,
    #             key=lambda a: getattr(a, ORDER_DICT[sort_column]),
    #             reverse=True,
    #         )
    # elif sort_column == 14:
    #     if sort_order == "asc":
    #         clients = sorted(clients, key=lambda a: a.monthly_patients)
    #     elif sort_order == "desc":
    #         clients = sorted(
    #             clients, key=lambda a: a.monthly_patients, reverse=True
    #         )
    # elif sort_column == 15:
    #     if sort_order == "asc":
    #         clients = sorted(clients, key=lambda a: a.potential_level)
    #     elif sort_order == "desc":
    #         clients = sorted(clients, key=lambda a: a.potential_level, reverse=True)

    # 对list进行分页
    paginator = Paginator(df.apply(lambda df: df.values, axis=1), length)
    # 把数据分成10个一页。
    try:
        hps = paginator.page(start / 10 + 1)
    # 请求页数错误
    except PageNotAnInteger:
        hps = paginator.page(1)
    except EmptyPage:
        hps = paginator.page(paginator.num_pages)
    data = []
    for item in hps:
        row = {
            "hp_id": item.hp_id
            # "bu": item.bu,
            # # "rd": item.rd,
            # "rm": item.rm,
            # "dsm": item.dsm,
            # "rsp": item.rsp,
            # # "xlt_id": item.xlt_id,
            # "hospital": item.hospital,
            # # "province": item.province,
            # # "dual_call": item.dual_call,
            # "hp_level": item.hp_level,
            # # "hp_access": item.hp_access,
            # "name": '<a href="/clientfile/clients/%s">%s</a>'
            # % (item.pk, item.name),
            # "dept": item.dept,
            # "title": item.title,
            # "consulting_times": item.consulting_times,
            # "patients_half_day": item.patients_half_day,
            # "target_prop": "{:.0%}".format(item.target_prop / 100),
            # "note": item.note,
            # "monthly_target_patients": item.monthly_patients,
            # "potential_level": potential_level,
        }
        data.append(row)
    dataTable["iTotalRecords"] = df.shape[0]  # 数据总条数
    dataTable["sEcho"] = sEcho + 1
    dataTable["iTotalDisplayRecords"] = df.shape[0]  # 显示的条数
    dataTable["aaData"] = data

    return HttpResponse(json.dumps(dataTable, ensure_ascii=False))


def get_df(form_dict, is_pivoted=True):
    sql = sqlparse(form_dict)  # sql拼接
    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe

    # df["HOSPITAL"] = df["HOSPITAL"].str[11:]  # 因医院全名太长，去除医院10位编码

    # if is_pivoted is True:
    #     return {
    #         "销售": pivot(df=df[df.TAG != "指标"], form_dict=form_dict),
    #         "社区销售": pivot(
    #             df=df[(df.TAG != "指标") & (df.LEVEL.isin(["旗舰社区", "普通社区"]))],
    #             form_dict=form_dict,
    #         ),
    #         "带指标销售": pivot(
    #             df=df[(df.TAG != "指标") & (df.PRODUCT.isin(PRODUCTS_HAVE_TARGET))],
    #             form_dict=form_dict,
    #         ),
    #         "指标": pivot(
    #             df=df[(df.TAG == "指标") & (df.PRODUCT.isin(PRODUCTS_HAVE_TARGET))],
    #             form_dict=form_dict,
    #         ),
    #         "社区指标": pivot(
    #             df=df[(df.TAG == "指标") & (df.LEVEL.isin(["旗舰社区", "普通社区"]))],
    #             form_dict=form_dict,
    #         ),
    #         "开户医院数": pivot(df=df[df.TAG != "指标"], form_dict=form_dict, type="count_hp"),
    #         "代表数": pivot(df=df[df.TAG != "指标"], form_dict=form_dict, type="count_rsp"),
    #     }

    # else:
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


def export(request, type):
    pass
