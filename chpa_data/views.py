from django.http import HttpResponse
from django.shortcuts import render
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import json
from django.utils import six
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from random import randrange
from pyecharts.charts import Bar
from pyecharts import options as opts
from .charts import *
from django.views.decorators.cache import cache_page

pd.set_option('display.max_columns', 5000)
pd.set_option('display.width', 5000)

ENGINE = create_engine('mssql+pymssql://(local)/CHPA_1806') #创建数据库连接引擎
DB_TABLE = 'data'

# 该字典key为前端准备显示的所有多选字段名, value为数据库对应的字段名
D_MULTI_SELECT = {
    'TC I': '[TC I]',
    'TC II': '[TC II]',
    'TC III': '[TC III]',
    'TC IV': '[TC IV]',
    '通用名|MOLECULE': 'MOLECULE',
    '商品名|PRODUCT': 'PRODUCT',
    '包装|PACKAGE': 'PACKAGE',
    '生产企业|CORPORATION': 'CORPORATION',
    '企业类型': 'MANUF_TYPE',
    '剂型': 'FORMULATION',
    '剂量': 'STRENGTH'
}

D_SINGLE_SELECT = {
    '分析维度': 'DIMENSION',
    '单位': 'UNIT',
    '周期': 'PERIOD',
}

D_TRANS = {
            'MAT': '滚动年',
            'QTR': '季度',
            'Value': '金额',
            'Volume': '盒数',
            'Volume (Counting Unit)': '最小制剂单位数',
            '滚动年': 'MAT',
            '季度': 'QTR',
            '金额': 'Value',
            '盒数': 'Volume',
            '最小制剂单位数': 'Volume (Counting Unit)'
           }
# def index(request):
#     sql = "Select count(*) from data" #标准sql语句，此处为测试返回数据库data表的数据条目n，之后可以用python处理字符串的方式动态扩展
#     df = pd.read_sql_query(sql, ENGINE) #将sql语句结果读取至Pandas Dataframe
#     context = {'data': df }
#     return render(request, 'display.html', context)


# @cache_page(60 * 60 * 24 * 90)
def index(request):
    mselect_dict = {}
    for key, value in D_MULTI_SELECT.items():
        mselect_dict[key] = {}
        mselect_dict[key]['select'] = value

    context = {
        'mselect_dict': mselect_dict
    }
    return render(request, 'display.html', context)


# def sqlparse(period, unit, filter_sql=None):
#     sql = "SELECT * FROM %s WHERE PERIOD = '%s' AND UNIT = '%s'" % (DB_TABLE, period, unit) # 必选的两个筛选字段
#     if filter_sql is not None:
#         sql = "%s And %s" % (sql, filter_sql) # 其他可选的筛选字段，如有则以And连接自定义字符串
#     return sql


def sqlparse(context):
    print(context)
    sql = "Select * from %s Where PERIOD = '%s' And UNIT = '%s'" % \
          (DB_TABLE, context['PERIOD_select'][0], context['UNIT_select'][0])  # 先处理单选部分

    # 下面循环处理多选部分
    for k, v in context.items():
        if k not in ['csrfmiddlewaretoken', 'DIMENSION_select', 'PERIOD_select', 'UNIT_select']:
            field_name = k[:-9]  # 字段名
            selected = v  # 选择项
            sql = sql_extent(sql, field_name, selected)  #未来可以通过进一步拼接字符串动态扩展sql语句
    return sql


def sql_extent(sql, field_name, selected, operator=" AND "):
    if selected is not None:
        statement = ''
        for data in selected:
            statement = statement + "'" + data + "', "
        statement = statement[:-2]
        if statement != '':
            sql = sql + operator + field_name + " in (" + statement + ")"
    return sql


# @cache_page(60 * 60 * 24 * 90)
def query(request):
    form_dict = dict(six.iterlists(request.GET))
    sql = sqlparse(form_dict)  # sql拼接
    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe
    print(df)
    dimension_selected = form_dict['DIMENSION_select'][0]
    if dimension_selected[0] == '[':

        column = dimension_selected[1:][:-1]
    else:
        column = dimension_selected

    pivoted = pd.pivot_table(df,
                             values='AMOUNT',  # 数据透视汇总值为AMOUNT字段，一般保持不变
                             index='DATE',  # 数据透视行为DATE字段，一般保持不变
                             columns=column,  # 数据透视列为前端选择的分析维度
                             aggfunc=np.sum)  # 数据透视汇总方式为求和，一般保持不变
    if pivoted.empty is False:
        pivoted.sort_values(by=pivoted.index[-1], axis=1, ascending=False, inplace=True)  # 结果按照最后一个DATE表现排序

    table = ptable(pivoted)
    table = table.to_html(formatters=build_formatters_by_col(table),  # 逐列调整表格内数字格式
                          classes='ui selectable celled table',  # 指定表格css class为Semantic UI主题
                          table_id='ptable'  # 指定表格id
                          )

    # Pyecharts交互图表
    bar_total_trend = json.loads(prepare_chart(pivoted, 'bar_total_trend', form_dict))

    # Matplotlib静态图表
    bubble_performance = prepare_chart(pivoted, 'bubble_performance', form_dict)
    context = {
        'market_size': kpi(pivoted)[0],
        'market_gr': kpi(pivoted)[1],
        'market_cagr': kpi(pivoted)[2],
        'ptable': table,
        'bar_total_trend': bar_total_trend,
        'bubble_performance': bubble_performance
    }

    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json charset=utf-8") # 返回结果必须是json格式


def kpi(df):
    # 市场按列求和，最后一行（最后一个DATE）就是最新的市场规模
    market_size = df.sum(axis=1).iloc[-1]
    # 市场按列求和，倒数第5行（倒数第5个DATE）就是同比的市场规模，可以用来求同比增长率
    market_gr = df.sum(axis=1).iloc[-1] / df.sum(axis=1).iloc[-5] - 1
    # 因为数据第一年是四年前的同期季度，时间序列收尾相除后开四次方根可得到年复合增长率
    market_cagr = (df.sum(axis=1).iloc[-1] / df.sum(axis=1).iloc[0]) ** (0.25) - 1
    if market_size == np.inf or market_size == -np.inf:
        market_size = 'N/A'
    if market_gr == np.inf or market_gr == -np.inf:
        market_gr = 'N/A'
    if market_cagr == np.inf or market_cagr == -np.inf:
        market_cagr = 'N/A'

    return [market_size, market_gr, market_cagr]


def ptable(df):
    # 份额
    df_share = df.transform(lambda x: x/x.sum(), axis=1)

    # 同比增长率，要考虑分子为0的问题
    df_gr = df.pct_change(periods=4)
    df_gr.dropna(how='all',inplace=True)
    df_gr.replace([np.inf, -np.inf], np.nan, inplace=True)

    # 最新滚动年绝对值表现及同比净增长
    df_latest = df.iloc[-1,:]
    df_latest_diff = df.iloc[-1,:] - df.iloc[-5,:]

    # 最新滚动年份额表现及同比份额净增长
    df_share_latest = df_share.iloc[-1, :]
    df_share_latest_diff = df_share.iloc[-1, :] - df_share.iloc[-5, :]

    # 进阶指标EI，衡量与市场增速的对比，高于100则为跑赢大盘
    df_gr_latest = df_gr.iloc[-1,:]
    df_total_gr_latest = (df.sum(axis=1).iloc[-1]/df.sum(axis=1).iloc[-5]) -1
    df_ei_latest = (df_gr_latest+1)/(df_total_gr_latest+1)*100

    df_combined = pd.concat([df_latest, df_latest_diff, df_share_latest, df_share_latest_diff, df_gr_latest, df_ei_latest], axis=1)
    df_combined.columns = ['最新滚动年销售额',
                           '净增长',
                           '份额',
                           '份额同比变化',
                           '同比增长率',
                           'EI']
    #准备数据表对象
    # table = df_combined.to_html(formatters=build_formatters_by_col(df_combined), classes='ui celled table', table_id='table')

    return df_combined


def get_distinct_list(column, db_table):
    sql = "Select DISTINCT " + column + " From " + db_table
    df = pd.read_sql_query(sql, ENGINE)
    l = df.values.flatten().tolist()
    return l


@cache_page(60 * 60 * 24 * 90)
def search(request, column, kw):
    sql = "SELECT DISTINCT TOP 10 %s FROM %s WHERE %s like '%%%s%%'" % (column, DB_TABLE, column, kw) # 返回不重复的前10个结果
    try:
        df = pd.read_sql_query(sql, ENGINE)
        l = df.values.flatten().tolist()
        results_list = []
        for element in l:
            option_dict = {'name': element,
                           'value': element,
                           }
            results_list.append(option_dict)
        res = {
            "success": True,
            "results": results_list,
            "code": 200,
        }
        print(l)
    except Exception as e:
        res = {
            "success": False,
            "errMsg": e,
            "code": 0,
        }
    return HttpResponse(json.dumps(res, ensure_ascii=False), content_type="application/json charset=utf-8") # 返回结果必须是json格式


def build_formatters_by_col(df):
    format_abs = lambda x: '{:,.0f}'.format(x)
    format_share = lambda x: '{:.1%}'.format(x)
    format_gr = lambda x: '{:.1%}'.format(x)
    format_currency = lambda x: '¥{:,.0f}'.format(x)
    d = {}
    for column in df.columns:
        if '份额' in column or '贡献' in column:
            d[column] = format_share
        elif '价格' in column or '单价' in column:
            d[column] = format_currency
        elif '同比增长' in column or '增长率' in column or 'CAGR' in column or '同比变化' in column:
            d[column] = format_gr
        else:
            d[column] = format_abs
    return d


def bar_base() -> Bar:
    c = (
        Bar()
        .add_xaxis(["衬衫", "羊毛衫", "雪纺衫", "裤子", "高跟鞋", "袜子"])
        .add_yaxis("商家A", [randrange(0, 100) for _ in range(6)])
        .add_yaxis("商家B", [randrange(0, 100) for _ in range(6)])
        .set_global_opts(title_opts=opts.TitleOpts(title="Bar-基本示例", subtitle="我是副标题"))
        .dump_options_with_quotes()
    )
    return c


def prepare_chart(df,  # 输入经过pivoted方法透视过的df，不是原始df
                  chart_type,  # 图表类型字符串，人为设置，根据图表类型不同做不同的Pandas数据处理，及生成不同的Pyechart对象
                  form_dict,  # 前端表单字典，用来获得一些变量作为图表的标签如单位
                  ):
    label = D_TRANS[form_dict['PERIOD_select'][0]] + D_TRANS[form_dict['UNIT_select'][0]]

    if chart_type == 'bar_total_trend':
        df_abs = df.sum(axis=1)  # Pandas列汇总，返回一个N行1列的series，每行是一个date的市场综合
        df_abs.index = df_abs.index.strftime("%Y-%m")  # 行索引日期数据变成2020-06的形式
        df_abs = df_abs.to_frame()  # series转换成df
        df_abs.columns = [label]  # 用一些设置变量为系列命名，准备作为图表标签
        df_gr = df.pct_change(periods=4)  # 获取同比增长率
        df_gr.dropna(how='all', inplace=True)  # 删除没有同比增长率的行，也就是时间序列数据的最前面几行，他们没有同比
        df_gr.replace([np.inf, -np.inf, np.nan], '-', inplace=True)  # 所有分母为0或其他情况导致的inf和nan都转换为'-'
        chart = echarts_stackbar(df=df_abs,
                                 df_gr=df_gr
                                 )  # 调用stackbar方法生成Pyecharts图表对象
        return chart.dump_options()  # 用json格式返回Pyecharts图表对象的全局设置
    elif chart_type == 'bubble_performance':
        df_abs = df.iloc[-1,:]  # 获取最新时间粒度的绝对值
        df_share = df.transform(lambda x: x / x.sum(), axis=1).iloc[-1,:] # 获取份额
        df_diff = df.diff(periods=4).iloc[-1,:]  # 获取同比净增长

        chart = mpl_bubble(x=df_abs,  # x轴数据
                           y=df_diff,  # y轴数据
                           z=df_share * 50000,  # 气泡大小数据
                           labels=df.columns.str.split('|').str[0],  # 标签数据
                           title='',  # 图表标题
                           x_title=label,  # x轴标题
                           y_title=label + '净增长',  # y轴标题
                           x_fmt='{:,.0f}',  # x轴格式
                           y_fmt='{:,.0f}',  # y轴格式
                           y_avg_line=True,  # 添加y轴分隔线
                           y_avg_value=0,  # y轴分隔线为y=0
                           label_limit=30  # 只显示前30个项目的标签
                           )
        return chart



