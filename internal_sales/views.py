from django.shortcuts import render, HttpResponse
from sqlalchemy import create_engine
import pandas as pd
import json
import numpy as np
from .models import *
import six
import datetime
from dateutil.relativedelta import relativedelta
from chpa_data.charts import *

ENGINE = create_engine("mssql+pymssql://(local)/Internal_sales")  # 创建数据库连接引擎
DB_TABLE = "data"
date = datetime.datetime(year=2020, month=11, day=1)
date_ya = date.replace(year=date.year - 1)  # 同比月份
date_year_begin = date.replace(month=1)  # 本年度开头
date_ya_begin = date_ya.replace(month=1)  # 去年开头

# 该字典为数据库字段名和Django Model的关联
D_MODEL = {
    "PROVINCE": Province,
    "CITY": City,
    "COUNTY": County,
    "HOSPITAL": Hospital,
    "PRODUCT": Product,
}


# 该字典key为前端准备显示的所有多选字段名, value为数据库对应的字段名
D_MULTI_SELECT = {
    "省份": "PROVINCE",
    "城市": "CITY",
    "区县": "COUNTY",
    "医院": "HOSPITAL",
    "产品": "PRODUCT",
}


# 该字典为数据分析的不同时间区间维度，键为其完完整命名，值为英文缩写
D_PERIOD = {
    "本年迄今YTD": "ytd",
    "滚动季MQT": "mqt",
    "单月MON": "mon",
}


def index(request):
    mselect_dict = {}
    for key, value in D_MULTI_SELECT.items():
        mselect_dict[key] = {}
        mselect_dict[key]["select"] = value

    context = {"date": date, "mselect_dict": mselect_dict, "period_dict": D_PERIOD}

    return render(request, "internal_sales/display.html", context)


def query(request):
    form_dict = dict(six.iterlists(request.GET))
    df_sales = get_df(form_dict)
    df_target = get_df(form_dict, "指标")

    # KPI字典
    kpi = get_kpi(df_sales, df_target)

    # 月度表现趋势表格
    table = get_ptable_monthly(df_sales)
    ptable_monthly = table.to_html(
        escape=False,
        formatters=build_formatters_by_col(table),  # 逐列调整表格内数字格式
        classes="ui selectable celled table",  # 指定表格css class为Semantic UI主题
        table_id="ptable_monthly",  # 指定表格id
    )

    # Pyecharts交互图表
    bar_total_monthly_trend = json.loads(prepare_chart(df_sales,df_target, "bar_total_monthly_trend", form_dict))
    pie_product = json.loads(prepare_chart(df_sales, df_target, "pie_product", form_dict))

    context = {
        "ptable_monthly": ptable_monthly,
        "bar_total_monthly_trend": bar_total_monthly_trend,
        'pie_product': pie_product
    }

    context = dict(context, **kpi)

    return HttpResponse(
        json.dumps(context, ensure_ascii=False), content_type="application/json charset=utf-8",
    )  # 返回结果必须是json格式


def get_ptable_monthly(df):
    df = df[df.index >= date_year_begin]
    df.index = df.index.strftime("%Y-%m")
    df = df.T
    df["趋势"] = None  # 表格最右侧预留Sparkline空列

    return df


def get_kpi(df_sales, df_target):
    kpi = {}

    for k, v in D_PERIOD.items():
        # 按列求和为查询总销售的Series
        sales_total = df_sales.sum(axis=1)
        # YTD销售
        sales = sales_total.loc[date_mask(df_sales, v)[0]].sum()
        # YTDYA销售
        sales_ya = sales_total.loc[date_mask(df_sales, v)[1]].sum()
        # YTD同比增长
        sales_gr = sales / sales_ya - 1

        # 按列求和为查询总指标的Series
        target_total = df_target.sum(axis=1)
        # YTD指标
        target = target_total.loc[date_mask(df_target, v)[0]].sum()
        # YTD达标率
        ach = sales / target

        kpi = dict(
            kpi,
            **{
                "sales_%s" % v: int(sales),
                "sales_gr_%s" % v: sales_gr,
                "target_%s" % v: int(target),
                "ach_%s" % v: ach,
            }
        )

    print(kpi)

    return kpi


def date_mask(df, period):
    if period == "ytd":
        mask = (df.index >= date_year_begin) & (df.index <= date)
        mask_ya = (df.index >= date_ya_begin) & (df.index <= date_ya)
    elif period == "mqt":
        mask = (df.index >= date + relativedelta(months=-3)) & (df.index <= date)
        mask_ya = (df.index >= date_ya + relativedelta(months=-3)) & (df.index <= date_ya)
    elif period == "mon":
        mask = df.index == date
        mask_ya = df.index == date_ya

    return mask, mask_ya


def get_df(form_dict, tag="销售", is_pivoted=True):
    sql = sqlparse(form_dict)  # sql拼接
    print(sql)
    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe

    # 区分销售和指标
    if tag == "销售":
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
            pivoted.fillna(0, inplace=True)

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


def prepare_chart(
    df_sales,  # 销售数据df, 输入经过pivoted方法透视过的df，不是原始df
    df_target, # 指标数据df
    chart_type,  # 图表类型字符串，人为设置，根据图表类型不同做不同的Pandas数据处理，及生成不同的Pyechart对象
    form_dict,  # 前端表单字典，用来获得一些变量作为图表的标签如单位
):
    SERIES_LIMIT = 10
    # label = D_TRANS[form_dict["PERIOD_select"][0]] + D_TRANS[form_dict["UNIT_select"][0]]

    if chart_type == "bar_total_monthly_trend":
        form_dict_by_product= form_dict.copy()
        form_dict_by_product["DIMENSION_select"] = ['PRODUCT']  # 前端控件交互字典将分析维度替换成PRODUCT

        df_sales_by_product = get_df(form_dict_by_product, tag="销售", is_pivoted=True).astype('int')
        df_sales_by_product.index = df_sales_by_product.index.strftime("%Y-%m")  # 行索引日期数据变成2020-06的形式
        # df_target_total = df_target.sum(axis=1)[:-1]  # 获取目标总和
        # df_target_total.index = df_target_total.index.strftime("%Y-%m")
        # df_ach_total = df_sales_total/df_target_total
        # df_ach_total.replace([np.inf, -np.inf, np.nan], "-", inplace=True)  # 所有分母为0或其他情况导致的inf和nan都转换为'-'
        #
        # df_sales_total = df_sales_total.to_frame()  # series转换成df
        # df_sales_total.columns = ['月度销售']
        # df_ach_total = df_ach_total.to_frame() # series转换成df
        # df_ach_total.columns = ['指标达成率']

        chart = echarts_stackbar(df=df_sales_by_product)  # 调用stackbar方法生成Pyecharts图表对象
        return chart.dump_options()  # 用json格式返回Pyecharts图表对象的全局设置
    elif chart_type == 'pie_product':
        form_dict_by_product= form_dict.copy()
        form_dict_by_product["DIMENSION_select"] = ['PRODUCT']  # 前端控件交互字典将分析维度替换成PRODUCT
        df_by_product = get_df(form_dict_by_product, tag="销售", is_pivoted=True)

        mask = date_mask(df_by_product, 'ytd')[0]
        df_by_product_ytd = df_by_product.loc[mask, :]
        df_by_product_ytd = df_by_product_ytd.sum(axis=0)
        # df_count = df['客户姓名'].groupby(df['所在科室']).count()
        # df_count = df_count.reindex(['心内科', '肾内科', '神内科', '内分泌科', '老干科', '其他科室'])
        chart = pie_radius(df_by_product_ytd)
        return chart.dump_options()  # 用json格式返回Pyecharts图表对象的全局设置
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