from django.shortcuts import render, HttpResponse
from django.http import request
from django.contrib.auth.decorators import login_required
from matplotlib.font_manager import json_dump
from sqlalchemy import create_engine
import pandas as pd
import json
import numpy as np
from .models import *
import six
import datetime
from dateutil.relativedelta import relativedelta
from chpa_data.charts import *
from .chart_class import PlotBubble
from datasite.commons import (
    NpEncoder,
    format_numbers,
    format_table,
    get_distinct_list,
    get_dt_page,
    sql_extent,
    qdict_to_dict,
    html_label,
)
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
    "潜力分位": "DECILE",
    # "经营类型": "OUTSOURCE"
    # "医院": "HOSPITAL",
    # "信立坦销售状态": "STATUS",
}


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
        主要包含生成前端控件多选的字段字典
    """
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
def query(request: request) -> HttpResponse:
    """根据前端控件的输入使用Ajax异步通信返回主要的查询内容

    Parameters
    ----------
    request : request
        前端控件的输入选择

    Returns
    -------
    HttpResponse
        返回json格式的数据和图表
    """
    form_dict = qdict_to_dict(request.GET)
    sql = sqlparse(form_dict)  # sql拼接
    data = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe
    dimension_selected = form_dict["DIMENSION_select"]  # 分析维度

    # 透视过的数据
    df = get_pivot(data, dimension_selected)

    # 气泡图展示的数量限制，如为0则不设限
    bubble_limit = (
        int(form_dict["bubble_limit"])
        if int(form_dict["bubble_limit"]) != 0
        else df.shape[0]
    )

    # KPIs
    kpi = {
        "潜力(DOT)": int(df["潜力(DOT)"].sum()),
        "终端数量": int(df["终端数量"].sum()),
        "信立坦目标终端覆盖潜力(DOT %)": df["信立坦目标终端潜力(DOT)"].sum() / df["潜力(DOT)"].sum(),
        "信立坦目标终端数": int(df["信立坦目标终端数"].sum()),
        "信立坦有量终端覆盖潜力(DOT %)": df["信立坦有量终端潜力(DOT)"].sum() / df["潜力(DOT)"].sum(),
        "信立坦有量终端数": int(df["信立坦有量终端数"].sum()),
        "信立坦所有终端份额(DOT %)": df["信立坦MAT销量(DOT)"].sum() / df["潜力(DOT)"].sum(),
        "信立坦目标终端份额(DOT %)": df["信立坦MAT销量(DOT)"].sum() / df["信立坦目标终端潜力(DOT)"].sum(),
        "信立坦有量终端份额(DOT %)": df["信立坦MAT销量(DOT)"].sum() / df["信立坦有量终端潜力(DOT)"].sum(),
    }

    # 综合透视分析表格
    table_pivot = df.fillna(0).reindex(
        columns=[
            # "终端数量",
            "潜力(DOT)",
            "潜力贡献(DOT %)",
            # "信立坦目标终端数",
            "信立坦目标终端覆盖潜力(DOT %)",
            # "信立坦有量终端数",
            "信立坦有量终端覆盖潜力(DOT %)",
            "信立坦MAT销量(DOT)",
            "信立坦销量贡献(DOT %)",
            "信立坦所有终端份额(DOT %)",
            "信立坦目标终端份额(DOT %)",
            "信立坦有量终端份额(DOT %)",
            "信立坦销量/潜力贡献比(所有终端)",
            "信立坦销量/潜力贡献比(有量终端)",
        ]
    )
    table_pivot = format_table(df=table_pivot, id="table_pivot")

    # 潜力详情分析表格
    table_pivot_potential = df.fillna(0).reindex(
        columns=[
            "终端数量",
            "潜力(DOT)",
            "潜力贡献(DOT %)",
            "信立坦目标终端数",
            "信立坦目标终端覆盖潜力(DOT %)",
            "信立坦有量终端数",
            "信立坦有量终端覆盖潜力(DOT %)",
            "信立坦有量终端覆盖目标潜力(DOT %)",
            "信立坦有量终端潜力贡献(DOT %)",
            "单家终端平均潜力(所有终端)",
            "单家终端平均潜力(有量终端)",
        ]
    )
    table_pivot_potential = format_table(
        df=table_pivot_potential, id="table_pivot_potential"
    )

    # 气泡图 - 潜力贡献（所有终端） versus 信立坦销量贡献
    fmt = [".1%"]
    plot_data = df.loc[:, ["潜力贡献(DOT %)", "信立坦销量贡献(DOT %)", "潜力(DOT)"]].fillna(0)
    plot_data = plot_data.sort_values(by="潜力(DOT)", ascending=False).head(bubble_limit)

    plot_bubble_contrib = plt.figure(
        FigureClass=PlotBubble,
        width=12,
        height=7,
        fmt=fmt,
        data=plot_data,
        fontsize=10,
        style={"xlabel": "潜力贡献(DOT %)\n气泡大小: 潜力(DOT)", "ylabel": "信立坦销量贡献(DOT %)"},
        save_to_str=True,
    ).plot(label_limit=30, show_reg=True)

    # 散点图 - 潜力贡献（有量终端） versus 信立坦销量贡献
    fmt = [".1%"]
    plot_data = df.loc[:, ["信立坦有量终端潜力贡献(DOT %)", "信立坦销量贡献(DOT %)", "潜力(DOT)"]].fillna(0)
    plot_data = plot_data.sort_values(by="信立坦有量终端潜力贡献(DOT %)", ascending=False).head(
        bubble_limit
    )

    plot_bubble_contrib2 = plt.figure(
        FigureClass=PlotBubble,
        width=12,
        height=7,
        fmt=fmt,
        data=plot_data,
        fontsize=10,
        style={
            "xlabel": "信立坦有量终端潜力贡献(DOT %)\n气泡大小: 潜力(DOT)",
            "ylabel": "信立坦销量贡献(DOT %)",
        },
        save_to_str=True,
    ).plot(label_limit=30, show_reg=True)

    # 散点图 - 信立坦有量终端覆盖潜力 versus 信立坦有量终端份额 （按信立坦销量排序）
    fmt = [".1%"]
    plot_data = df.loc[
        :, ["信立坦有量终端覆盖潜力(DOT %)", "信立坦有量终端份额(DOT %)", "信立坦MAT销量(DOT)"]
    ].fillna(0)
    plot_data = plot_data.sort_values(by="信立坦MAT销量(DOT)", ascending=False).head(
        bubble_limit
    )

    plot_bubble_allocation = plt.figure(
        FigureClass=PlotBubble,
        width=12,
        height=7,
        fmt=fmt,
        data=plot_data,
        fontsize=10,
        style={
            "xlabel": "信立坦有量终端覆盖潜力(DOT %)\n气泡大小: 信立坦MAT销量(DOT)",
            "ylabel": "信立坦有量终端份额(DOT %)",
        },
        save_to_str=True,
    ).plot(
        label_limit=30,
        x_avg_line=True,
        x_avg_value=kpi["信立坦有量终端覆盖潜力(DOT %)"],
        x_avg_label="平均:%s" % "{:.1%}".format(kpi["信立坦有量终端覆盖潜力(DOT %)"]),
        y_avg_line=True,
        y_avg_value=kpi["信立坦有量终端份额(DOT %)"],
        y_avg_label="平均:%s" % "{:.1%}".format(kpi["信立坦有量终端份额(DOT %)"]),
    )

    # 散点图 - 信立坦有量终端覆盖潜力 versus 信立坦有量终端份额 （按潜力排序）
    fmt = [".1%"]
    plot_data = df.loc[:, ["信立坦有量终端覆盖潜力(DOT %)", "信立坦有量终端份额(DOT %)", "潜力(DOT)"]].fillna(
        0
    )
    plot_data = plot_data.sort_values(by="潜力(DOT)", ascending=False).head(bubble_limit)

    plot_bubble_allocation2 = plt.figure(
        FigureClass=PlotBubble,
        width=12,
        height=7,
        fmt=fmt,
        data=plot_data,
        fontsize=10,
        style={
            "xlabel": "信立坦有量终端覆盖潜力(DOT %)\n气泡大小: 潜力(DOT)",
            "ylabel": "信立坦有量终端份额(DOT %)",
        },
        save_to_str=True,
    ).plot(
        label_limit=30,
        x_avg_line=True,
        x_avg_value=kpi["信立坦有量终端覆盖潜力(DOT %)"],
        x_avg_label="平均:%s" % "{:.1%}".format(kpi["信立坦有量终端覆盖潜力(DOT %)"]),
        y_avg_line=True,
        y_avg_value=kpi["信立坦有量终端份额(DOT %)"],
        y_avg_label="平均:%s" % "{:.1%}".format(kpi["信立坦有量终端份额(DOT %)"]),
    )

    # # Echarts Grid 散点图，展示不同维度内的单家终端潜力
    # plot_scatter = echarts_scatter(
    #     data[["HP_NAME", "POTENTIAL_DOT", "MAT_SALES"]].set_index("HP_NAME").fillna(0)
    # )

    # # 是否只显示前200条结果，显示过多结果会导致前端渲染性能不足
    # show_limit_results = form_dict["toggle_limit_show"]

    # json不支持nan和inf，替换为None
    for k, v in kpi.items():
        if v in [np.inf, -np.inf, np.nan] or np.isnan(v):
            kpi[k] = None

    context = {
        "bubble_limit": bubble_limit,
        "bubble_limit_works": bubble_limit < df.shape[0],
        "kpi": kpi,
        "table_pivot": table_pivot,
        "table_pivot_potential": table_pivot_potential,
        "plot_bubble_contrib": plot_bubble_contrib,
        "plot_bubble_contrib2": plot_bubble_contrib2,
        "plot_bubble_allocation": plot_bubble_allocation,
        "plot_bubble_allocation2": plot_bubble_allocation2,
        # "plot_scatter": json.loads(plot_scatter.dump_options()),
    }

    return HttpResponse(
        json.dumps(context, ensure_ascii=False),
        content_type="application/json charset=utf-8",
    )  # 返回结果必须是json格式


@login_required
def export(request: request, type: str) -> HttpResponse:
    """根据前端控件的输入使用导出选择范围内的数据，数据有2种格式——原始数 or 透视&计算过的表格数据

    Parameters
    ----------
    request : request
        前端控件的输入选择
    type : str
        以何种格式导出——原始数 or 透视&计算过的表格数据

    Returns
    -------
    HttpResponse
        Excel格式的下载内容
    """

    form_dict = qdict_to_dict(request.GET)
    sql = sqlparse(form_dict)  # sql拼接
    data = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe
    dimension_selected = form_dict["DIMENSION_select"]  # 分析维度

    excel_file = IO()
    xlwriter = pd.ExcelWriter(excel_file, engine="xlsxwriter")

    if type == "pivoted":
        df = get_pivot(data, dimension_selected)  # 透视后的数据
        df.to_excel(xlwriter, sheet_name="data", index=True)
    elif type == "raw":
        data.to_excel(xlwriter, sheet_name="data", index=False)

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


@login_required()
def table_hp(request: request) -> HttpResponse:
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
    form_dict = json.loads(request.POST.get("formdata"))  # filter栏表单数据
    sql = sqlparse(form_dict)  # sql拼接
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
        0: "HP_ID",
        1: "HP_NAME",
        2: "PROVINCE",
        3: "CITY",
        4: "COUNTY",
        5: "AM",
        6: "RSP",
        7: "HP_TYPE",
        8: "STATUS",
        9: "DECILE",
        10: "POTENTIAL_DOT",
        11: "MAT_SALES",
        12: "SHARE",
    }

    result = get_dt_page(df, aodata, dict_order)

    data = []
    for item in result:
        row = {
            "hp_id": item["HP_ID"],
            "hp_name": item["HP_NAME"],
            "province": item["PROVINCE"],
            "city": item["CITY"],
            "county": item["COUNTY"],
            "am": item["AM"],
            "rsp": item["RSP"],
            "hp_type": html_label(item["HP_TYPE"]),
            "status": html_label(
                "目标" if item["STATUS"] in ["有销量目标医院", "无销量目标医院"] else "非目标"
            ),
            "decile": html_label(item["DECILE"]),
            "potential_dot": "{:,.0f}".format(item["POTENTIAL_DOT"])
            if item["POTENTIAL_DOT"] is not None
            else "0",
            "mat_sales": "{:,.0f}".format(item["MAT_SALES"])
            if item["MAT_SALES"] is not None
            else "0",
            "share": "{:.1%}".format(item["SHARE"])
            if item["SHARE"] is not None
            else "0.0%",
        }
        data.append(row)

    dataTable = {}
    dataTable["iTotalRecords"] = df.shape[0]  # 数据总条数
    dataTable["sEcho"] = sEcho + 1
    dataTable["iTotalDisplayRecords"] = df.shape[0]  # 显示的条数
    dataTable["aaData"] = data

    return HttpResponse(json.dumps(dataTable, ensure_ascii=False))


# @login_required()
# def table_pivot(request):
#     form_dict = json.loads(request.POST.get("formdata"))  # filter栏表单数据
#     sql = sqlparse(form_dict)  # sql拼接
#     df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe

#     # 检查查询是否有数据，如没有，返回null;如有，继续可视化
#     if df.empty:
#         dataTable = {}
#         dataTable["iTotalRecords"] = 0  # 数据总条数
#         dataTable["sEcho"] = 0
#         dataTable["iTotalDisplayRecords"] = 0  # 显示的条数
#         dataTable["aaData"] = []
#         return HttpResponse(
#             json.dumps(dataTable), content_type="application/json charset=utf-8",
#         )

#     dimension_selected = form_dict["DIMENSION_select"]  # 分析维度

#     # 潜力部分
#     pivoted_potential = pd.pivot_table(
#         data=df,
#         values="POTENTIAL_DOT",
#         index=dimension_selected,
#         columns=None,
#         aggfunc=[len, sum],
#         fill_value=0,
#     )

#     pivoted_potential = pd.DataFrame(
#         pivoted_potential.to_records()
#     )  # pivot table对象转为默认df
#     pivoted_potential.set_index(dimension_selected, inplace=True)
#     pivoted_potential.columns = ["终端数量", "潜力(DOT)"]
#     pivoted_potential["潜力贡献(DOT %)"] = (
#         pivoted_potential["潜力(DOT)"] / pivoted_potential["潜力(DOT)"].sum()
#     )
#     # pivoted_potential.reset_index(inplace=True)

#     # 覆盖部分
#     pivoted_access = pd.pivot_table(
#         data=df,
#         values="POTENTIAL_DOT",
#         index=dimension_selected,
#         columns="STATUS",
#         aggfunc=[len, sum],
#         fill_value=0,
#     )
#     pivoted_access = pd.DataFrame(pivoted_access.to_records())  # pivot table对象转为默认df
#     pivoted_access.set_index(dimension_selected, inplace=True)
#     pivoted_access = pivoted_access.reindex(
#         columns=[
#             "('len', '无销量目标医院')",
#             "('len', '有销量目标医院')",
#             "('len', '非目标医院')",
#             "('sum', '无销量目标医院')",
#             "('sum', '有销量目标医院')",
#             "('sum', '非目标医院')",
#         ]
#     ).fillna(0)
#     pivoted_access.columns = [
#         "信立坦无量终端数",
#         "信立坦有量终端数",
#         "信立坦非目标终端数",
#         "信立坦无量终端潜力(DOT)",
#         "信立坦有量终端潜力(DOT)",
#         "信立坦非目标终端潜力(DOT)",
#     ]
#     print(pivoted_access)
#     pivoted_access["信立坦目标终端数"] = pivoted_access["信立坦无量终端数"] + pivoted_access["信立坦有量终端数"]
#     pivoted_access["信立坦目标终端潜力(DOT)"] = (
#         pivoted_access["信立坦无量终端潜力(DOT)"] + pivoted_access["信立坦有量终端潜力(DOT)"]
#     )
#     pivoted_access["信立坦目标终端覆盖潜力(DOT %)"] = pivoted_access[
#         "信立坦目标终端潜力(DOT)"
#     ] / pivoted_access.sum(axis=1)
#     pivoted_access["信立坦有量终端覆盖潜力(DOT %)"] = pivoted_access[
#         "信立坦有量终端潜力(DOT)"
#     ] / pivoted_access.sum(axis=1)
#     # pivoted_access.reset_index(inplace=True)

#     # 内部销售部分
#     pivoted_sales = pd.pivot_table(
#         data=df,
#         values="MAT_SALES",
#         index=dimension_selected,
#         columns=None,
#         aggfunc=sum,
#         fill_value=0,
#     )
#     pivoted_sales = pd.DataFrame(pivoted_sales.to_records())  # pivot table对象转为默认df
#     pivoted_sales.set_index(dimension_selected, inplace=True)
#     pivoted_sales.columns = ["信立坦MAT销量(DOT)"]
#     pivoted_sales["信立坦销量贡献(DOT %)"] = (
#         pivoted_sales["信立坦MAT销量(DOT)"] / pivoted_sales["信立坦MAT销量(DOT)"].sum()
#     )

#     df_combined = pd.concat([pivoted_potential, pivoted_access, pivoted_sales], axis=1)
#     df_combined["信立坦所有终端份额"] = df_combined["信立坦MAT销量(DOT)"] / df_combined["潜力(DOT)"]

#     df_combined["信立坦目标终端份额"] = (
#         df_combined["信立坦MAT销量(DOT)"] / df_combined["信立坦目标终端潜力(DOT)"]
#     )

#     df_combined["信立坦有量终端份额"] = (
#         df_combined["信立坦MAT销量(DOT)"] / df_combined["信立坦有量终端潜力(DOT)"]
#     )

#     df_combined.fillna(0, inplace=True)
#     df_combined.reset_index(inplace=True)

#     aodata = json.loads(request.POST.get("aodata"))
#     for item in aodata:
#         if item["name"] == "sEcho":
#             sEcho = int(item["value"])  # 客户端发送的标识

#     # 排序字典，前端点击排序的列索引映射到df字段名
#     dict_order = {
#         0: dimension_selected,
#         1: "HP_NUMBER",
#         2: "POTENTIAL_DOT",
#         3: "POTENTIAL_CONTRIB",
#         4: "HP_NUMBER_TARGET",
#         5: "COVERAGE_TARGET",
#         6: "HP_NUMBER_HAVE_SALES",
#         7: "COVERAGE_HAVE_SALES",
#         8: "SALES_DOT",
#         9: "SALES_CONTRIB",
#         10: "SHARE_TOTAL",
#         11: "SHARE_TARGET",
#         12: "SHARE_HAVE_SALES",
#     }

#     result = get_dt_page(df_combined, aodata, dict_order)

#     data = []
#     for item in result:
#         row = {
#             dimension_selected: item[dimension_selected],  # 分析维度
#             "HP_NUMBER": format_numbers(  # 所有终端数量
#                 num_str=item["HP_NUMBER"],
#                 format_str="{:,.0f}",
#                 else_str="0",
#                 ignore_nan=True,
#             ),
#             "POTENTIAL_DOT": format_numbers(  # 潜力
#                 num_str=item["POTENTIAL_DOT"],
#                 format_str="{:,.0f}",
#                 else_str="0",
#                 ignore_nan=True,
#             ),
#             "POTENTIAL_CONTRIB": format_numbers(  # 潜力贡献
#                 num_str=item["POTENTIAL_CONTRIB"],
#                 format_str="{:.1%}",
#                 else_str="0.0%",
#                 ignore_nan=True,
#             ),
#             "HP_NUMBER_TARGET": format_numbers(  # 信立坦目标终端数量
#                 num_str=item["HP_NUMBER_TARGET"],
#                 format_str="{:,.0f}",
#                 else_str="0",
#                 ignore_nan=True,
#             ),
#             "COVERAGE_TARGET": format_numbers(  # 信立坦目标终端覆盖潜力(DOT %)
#                 num_str=item["COVERAGE_TARGET"],
#                 format_str="{:.1%}",
#                 else_str="0.0%",
#                 ignore_nan=True,
#             ),
#             "HP_NUMBER_HAVE_SALES": format_numbers(  # 信立坦有量终端数量
#                 num_str=item["HP_NUMBER_HAVE_SALES"],
#                 format_str="{:,.0f}",
#                 else_str="0",
#                 ignore_nan=True,
#             ),
#             "COVERAGE_HAVE_SALES": format_numbers(  # 信立坦有量终端覆盖潜力(DOT %)
#                 num_str=item["COVERAGE_HAVE_SALES"],
#                 format_str="{:.1%}",
#                 else_str="0.0%",
#                 ignore_nan=True,
#             ),
#             "SALES_DOT": format_numbers(  # MAT销量
#                 num_str=item["SALES_DOT"],
#                 format_str="{:,.0f}",
#                 else_str="0",
#                 ignore_nan=True,
#             ),
#             "SALES_CONTRIB": format_numbers(  # 信立坦销量贡献
#                 num_str=item["SALES_CONTRIB"],
#                 format_str="{:.1%}",
#                 else_str="0.0%",
#                 ignore_nan=True,
#             ),
#             "SHARE_TOTAL": format_numbers(  # 信立坦所有终端份额(DOT %)
#                 num_str=item["SHARE_TOTAL"],
#                 format_str="{:.1%}",
#                 else_str="0.0%",
#                 ignore_nan=True,
#             ),
#             "SHARE_TARGET": format_numbers(  # 信立坦目标终端份额(DOT %)
#                 num_str=item["SHARE_TARGET"],
#                 format_str="{:.1%}",
#                 else_str="0.0%",
#                 ignore_nan=True,
#             ),
#             "SHARE_HAVE_SALES": format_numbers(  # 信立坦有量终端份额(DOT %)
#                 num_str=item["SHARE_HAVE_SALES"],
#                 format_str="{:.1%}",
#                 else_str="0.0%",
#                 ignore_nan=True,
#             ),
#         }
#         data.append(row)

#     # print(data)

#     dataTable = {}
#     dataTable["iTotalRecords"] = df_combined.shape[0]  # 数据总条数
#     dataTable["sEcho"] = sEcho + 1
#     dataTable["iTotalDisplayRecords"] = df_combined.shape[0]  # 显示的条数
#     dataTable["aaData"] = data

#     return HttpResponse(json.dumps(dataTable, ensure_ascii=False))


def get_pivot(df: pd.DataFrame, dimension_selected: str) -> pd.DataFrame:
    """透视处理数据，以计算各种潜力、覆盖、上量相关的KPIs

    Parameters
    ----------
    df : pd.DataFrame
        原始数据（每行为1个终端）
    dimension_selected : str
        前端控件返回的分析维度，即透视的行字段

    Returns
    -------
    pd.DataFrame
        行为分析维度，列为各种潜力、覆盖、上量相关的KPIs的df
    """

    # 检查查询是否有数据，如没有，返回null;如有，继续可视化
    if df.empty:
        return None

    # 潜力部分
    pivoted_potential = pd.pivot_table(
        data=df,
        values="POTENTIAL_DOT",
        index=dimension_selected,
        columns=None,
        aggfunc=[len, sum],
        fill_value=0,
    )

    pivoted_potential = pd.DataFrame(
        pivoted_potential.to_records()
    )  # pivot table对象转为默认df
    pivoted_potential.set_index(dimension_selected, inplace=True)
    pivoted_potential.columns = ["终端数量", "潜力(DOT)"]
    pivoted_potential["潜力贡献(DOT %)"] = (
        pivoted_potential["潜力(DOT)"] / pivoted_potential["潜力(DOT)"].sum()
    )
    # pivoted_potential.reset_index(inplace=True)

    # 覆盖部分
    pivoted_access = pd.pivot_table(
        data=df,
        values="POTENTIAL_DOT",
        index=dimension_selected,
        columns="STATUS",
        aggfunc=[len, sum],
        fill_value=0,
    )
    pivoted_access = pd.DataFrame(pivoted_access.to_records())  # pivot table对象转为默认df
    pivoted_access.set_index(dimension_selected, inplace=True)
    pivoted_access = pivoted_access.reindex(
        columns=[
            "('len', '无销量目标医院')",
            "('len', '有销量目标医院')",
            "('len', '非目标医院')",
            "('sum', '无销量目标医院')",
            "('sum', '有销量目标医院')",
            "('sum', '非目标医院')",
        ]
    ).fillna(0)
    pivoted_access.columns = [
        "信立坦无量终端数",
        "信立坦有量终端数",
        "信立坦非目标终端数",
        "信立坦无量终端潜力(DOT)",
        "信立坦有量终端潜力(DOT)",
        "信立坦非目标终端潜力(DOT)",
    ]
    pivoted_access["信立坦目标终端数"] = pivoted_access["信立坦无量终端数"] + pivoted_access["信立坦有量终端数"]
    pivoted_access["信立坦目标终端潜力(DOT)"] = (
        pivoted_access["信立坦无量终端潜力(DOT)"] + pivoted_access["信立坦有量终端潜力(DOT)"]
    )
    pivoted_access["信立坦目标终端覆盖潜力(DOT %)"] = (
        pivoted_access["信立坦目标终端潜力(DOT)"] / pivoted_potential["潜力(DOT)"]
    )
    pivoted_access["信立坦有量终端覆盖潜力(DOT %)"] = (
        pivoted_access["信立坦有量终端潜力(DOT)"] / pivoted_potential["潜力(DOT)"]
    )
    # pivoted_access.reset_index(inplace=True)

    # 内部销售部分
    pivoted_sales = pd.pivot_table(
        data=df,
        values="MAT_SALES",
        index=dimension_selected,
        columns=None,
        aggfunc=sum,
        fill_value=0,
    )
    pivoted_sales = pd.DataFrame(pivoted_sales.to_records())  # pivot table对象转为默认df
    pivoted_sales.set_index(dimension_selected, inplace=True)
    pivoted_sales.columns = ["信立坦MAT销量(DOT)"]
    pivoted_sales["信立坦销量贡献(DOT %)"] = (
        pivoted_sales["信立坦MAT销量(DOT)"] / pivoted_sales["信立坦MAT销量(DOT)"].sum()
    )

    df_combined = pd.concat([pivoted_potential, pivoted_access, pivoted_sales], axis=1)
    df_combined["信立坦所有终端份额(DOT %)"] = (
        df_combined["信立坦MAT销量(DOT)"] / df_combined["潜力(DOT)"]
    )

    df_combined["信立坦目标终端份额(DOT %)"] = (
        df_combined["信立坦MAT销量(DOT)"] / df_combined["信立坦目标终端潜力(DOT)"]
    )

    df_combined["信立坦有量终端份额(DOT %)"] = (
        df_combined["信立坦MAT销量(DOT)"] / df_combined["信立坦有量终端潜力(DOT)"]
    )

    df_combined["信立坦有量终端潜力贡献(DOT %)"] = (
        df_combined["信立坦有量终端潜力(DOT)"] / df_combined["信立坦有量终端潜力(DOT)"].sum()
    )

    df_combined["信立坦销量/潜力贡献比(所有终端)"] = (
        df_combined["信立坦销量贡献(DOT %)"] / df_combined["潜力贡献(DOT %)"]
    )

    df_combined["信立坦销量/潜力贡献比(有量终端)"] = (
        df_combined["信立坦销量贡献(DOT %)"] / df_combined["信立坦有量终端潜力贡献(DOT %)"]
    )

    df_combined["信立坦有量终端覆盖目标潜力(DOT %)"] = (
        df_combined["信立坦有量终端潜力(DOT)"] / df_combined["信立坦目标终端潜力(DOT)"]
    )

    df_combined["单家终端平均潜力(所有终端)"] = df_combined["潜力(DOT)"] / df_combined["终端数量"]

    df_combined["单家终端平均潜力(有量终端)"] = (
        df_combined["信立坦有量终端潜力(DOT)"] / df_combined["信立坦有量终端数"]
    )
    # df_combined.replace([np.inf, -np.inf], np.nan, inplace=True)  # 因分母为0除法产生的inf和-inf替换成nan

    return df_combined


def sqlparse(context: dict, columns: list = None) -> str:
    """根据前端控件的输入返回从sql数据库取数的sql语句

    Parameters
    ----------
    context : dict
        前端控件输入含有各字段条件参数的字典
    columns : list, optional
        指定数据库取数的字段, by default None

    Returns
    -------
    str
        取数的sql语句
    """
    if columns is None:
        sql_columns = "*"
    else:
        sql_columns = ", ".join(columns)
    sql = f"Select {sql_columns} from %s WHERE 1=1" % DB_TABLE  # 先处理单选部分
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
                "bubble_limit",
                "scatter_limit",
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


@login_required()
def scatter_data(request: request) -> HttpResponse:
    """根据前端控件的输入使用Ajax异步通信返回为终端表现散点图准备的数据

    Parameters
    ----------
    request : request
        前端控件的输入选择

    Returns
    -------
    HttpResponse
        json格式的单家终端数据
    """

    form_dict = json.loads(request.POST.get("formdata"))  # filter栏表单数据
    sql = sqlparse(
        form_dict,
        [
            "HP_NAME",
            "STATUS",
            "POTENTIAL_DOT",
            "MAT_SALES",
            "AM",
            "RSP",
            "HP_TYPE",
            "DECILE",
        ],
    )  # sql拼接
    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe

    df = df.fillna(0)
    df[["POTENTIAL_DOT", "MAT_SALES"]] = df[["POTENTIAL_DOT", "MAT_SALES"]].astype(
        "int"
    )

    context = {"data": df.values.tolist(), "sales_max": df["MAT_SALES"].max()}

    return HttpResponse(
        json.dumps(context, cls=NpEncoder, ensure_ascii=False),
        content_type="application/json charset=utf-8",
    )
