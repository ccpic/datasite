from django.shortcuts import render, HttpResponseRedirect
from sqlalchemy import create_engine
import pandas as pd
import json
import six
from django.http import HttpResponse
from .charts import *
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
import datetime
from .models import *
try:
    from io import BytesIO as IO # for modern python
except ImportError:
    from io import StringIO as IO # for legacy python

pd.set_option('display.max_columns', 5000)
pd.set_option('display.width', 5000)

ENGINE = create_engine('mssql+pymssql://(local)/CHPA_1806') #创建数据库连接引擎
DB_TABLE = 'data'


# 该字典为数据库字段名和Django Model的关联
D_MODEL = {
    '[TC I]': TC_I,
    '[TC II]': TC_II,
    '[TC III]': TC_III,
    '[TC IV]': TC_IV,
    'MOLECULE': Molecule,
    'PRODUCT': Product,
    'PACKAGE': Package,
    'CORPORATION': Corporation,
    'MANUF_TYPE': Manuf_type,
    'FORMULATION': Formulation,
    'STRENGTH': Strength,
    'MOLECULE_TC': Molecule_TC,
    'PRODUCT_CORP': Product_Corp
}

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



# @login_required
# def index(request):
#     return render(request, 'tenders.html')


# @login_required
def index(request):
    mselect_dict = {}
    for key, value in D_MULTI_SELECT.items():
        mselect_dict[key] = {}
        mselect_dict[key]['select'] = value

    context = {
        'mselect_dict': mselect_dict
    }
    return render(request, 'chpa_data/display.html', context)


# @login_required
@cache_page(60 * 60 * 24 * 90)
def query(request):
    print(request.GET)
    form_dict = dict(six.iterlists(request.GET))
    label = D_TRANS[form_dict['PERIOD_select'][0]] + D_TRANS[form_dict['UNIT_select'][0]] # 分析时间段+单位组成数据标签
    pivoted = get_df(form_dict)

    # 最新横截面表现表格
    table = get_ptable(pivoted, label)
    ptable = table.to_html(formatters=build_formatters_by_col(table),  # 逐列调整表格内数字格式
                          classes='ui selectable celled table',  # 指定表格css class为Semantic UI主题
                          table_id='ptable'  # 指定表格id
                          )

    # 趋势表现表格
    table = get_ptable_trend(pivoted, label)
    ptable_trend = table.to_html(formatters=build_formatters_by_col(table),  # 逐列调整表格内数字格式
                          classes='ui selectable celled table',  # 指定表格css class为Semantic UI主题
                          table_id='ptable_trend'  # 指定表格id
                          )

    # 价格分析表格
    table = get_price(form_dict, 'Volume')
    price_table_box = table.to_html(formatters=build_formatters_by_col(table),  # 逐列调整表格内数字格式
                          classes='ui selectable celled table',  # 指定表格css class为Semantic UI主题
                          table_id='price_table_box'  # 指定表格id
                          )
    table = get_price(form_dict, 'Volume (Counting Unit)')
    price_table_cnt = table.to_html(formatters=build_formatters_by_col(table),  # 逐列调整表格内数字格式
                          classes='ui selectable celled table',  # 指定表格css class为Semantic UI主题
                          table_id='price_table_cnt'  # 指定表格id
                          )

    # Pyecharts交互图表
    bar_total_trend = json.loads(prepare_chart(pivoted, 'bar_total_trend', form_dict))
    stackarea_abs_trend = json.loads(prepare_chart(pivoted, 'stackarea_abs_trend', form_dict))
    stackarea_share_trend = json.loads(prepare_chart(pivoted, 'stackarea_share_trend', form_dict))
    line_gr_trend = json.loads(prepare_chart(pivoted, 'line_gr_trend', form_dict))

    context = {
        'label': label,
        'market_size': kpi(pivoted)[0],
        'market_gr': kpi(pivoted)[1],
        'market_cagr': kpi(pivoted)[2],
        'ptable': ptable,
        'ptable_trend': ptable_trend,
        'price_table_box': price_table_box,
        'price_table_cnt': price_table_cnt,
        'bar_total_trend': bar_total_trend,
        'stackarea_abs_trend': stackarea_abs_trend,
        'stackarea_share_trend': stackarea_share_trend,
        'line_gr_trend': line_gr_trend
    }

    # 根据查询选线决定是否展示Matplotlib静态图表
    if form_dict['toggle_bubble_perf'][0] == 'true':
        bubble_performance = prepare_chart(pivoted, 'bubble_performance', form_dict)
        context['bubble_performance'] = bubble_performance

    return HttpResponse(json.dumps(context, ensure_ascii=False), content_type="application/json charset=utf-8") # 返回结果必须是json格式


# @login_required
@cache_page(60 * 60 * 24 * 90)
def search(request, column, kw):
    # sql = "SELECT DISTINCT TOP 20 %s FROM %s WHERE %s like '%%%s%%'" % (column, DB_TABLE, column, kw) # 返回不重复的前10个结果
    try:
        # df = pd.read_sql_query(sql, ENGINE)
        # l = df.values.flatten().tolist()
        m = D_MODEL[column]
        results = m.objects.filter(name__contains=kw)
        l = results.values_list('name')
        print(l)
        results_list = []
        for item in l:
            option_dict = {'name': item,
                           'value': item,
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
    return HttpResponse(json.dumps(res, ensure_ascii=False), content_type="application/json charset=utf-8") # 返回结果必须是json格式


# @login_required
def export(request, type):
    form_dict = dict(six.iterlists(request.GET))

    if type == 'pivoted':
        df = get_df(form_dict)  # 透视后的数据
    elif type == 'raw':
        df = get_df(form_dict, is_pivoted=False)  # 原始数

    excel_file = IO()

    xlwriter = pd.ExcelWriter(excel_file, engine='xlsxwriter')

    df.to_excel(xlwriter, 'data', index=True)

    xlwriter.save()
    xlwriter.close()

    excel_file.seek(0)

    # 设置浏览器mime类型
    response = HttpResponse(excel_file.read(),
                            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # 设置文件名
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 当前精确时间不会重复，适合用来命名默认导出文件
    response['Content-Disposition'] = 'attachment; filename=' + now + '.xlsx'
    return response


def sqlparse(context):
    print(context)
    sql = "Select * from %s Where PERIOD = '%s' And UNIT = '%s'" % \
          (DB_TABLE, context['PERIOD_select'][0], context['UNIT_select'][0])  # 先处理单选部分

    # 下面循环处理多选部分
    for k, v in context.items():
        if k not in ['csrfmiddlewaretoken', 'DIMENSION_select', 'PERIOD_select', 'UNIT_select', 'lang', 'toggle_bubble_perf']:
            if k[-2:] == '[]':
                field_name = k[:-9]  # 如果键以[]结尾，删除_select[]取原字段名
            else:
                field_name = k[:-7]  # 如果键不以[]结尾，删除_select取原字段名
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


def get_df(form_dict, is_pivoted=True):
    sql = sqlparse(form_dict)  # sql拼接
    df = pd.read_sql_query(sql, ENGINE)  # 将sql语句结果读取至Pandas Dataframe

    #  根据中英文选项调整内容
    if form_dict['lang'][0] == 'CN':
        df['TC I'] = df['TC I'].str[:2]+df['TC I'].str.split('|').str[1]
        df['TC II'] = df['TC II'].str[:4] + df['TC II'].str.split('|').str[1]
        df['TC III'] = df['TC III'].str[:5] + df['TC III'].str.split('|').str[1]
        df['TC IV'] = df['TC IV'].str[:6] + df['TC IV'].str.split('|').str[1]
        df['MOLECULE'] = df['MOLECULE'].str.split('|').str[0]
        df['PRODUCT'] = df['PRODUCT'].str.split('|').str[0] + '(' + df['PRODUCT'].str.split('|').str[1].str[-3:] + ')'
        df['CORPORATION'] = df['CORPORATION'].str.split('|').str[0]
        df['PRODUCT_CORP'] = df['PRODUCT_CORP'].str.split(' （').str[0].str.split('|').str[0]+' （'+df['PRODUCT_CORP'].str.split(' （').str[1].str.split('|').str[0]+'）'
        df['MOLECULE_TC'] = df['MOLECULE_TC'].str.split('|').str[0]+' （'+df['MOLECULE_TC'].str.split(' （').str[1]
    elif form_dict['lang'][0] == 'EN':
        df['TC I'] = df['TC I'].str.split('|').str[0]
        df['TC II'] = df['TC II'].str.split('|').str[0]
        df['TC III'] = df['TC III'].str.split('|').str[0]
        df['TC IV'] = df['TC IV'].str.split('|').str[0]
        df['MOLECULE'] = df['MOLECULE'].str.split('|').str[1]
        df['PRODUCT'] = df['PRODUCT'].str.split('|').str[1]
        df['CORPORATION'] = df['CORPORATION'].str.split('|').str[1]
        df['PRODUCT_CORP'] = df['PRODUCT_CORP'].str.split(' （').str[0].str.split('|').str[1]+' （'+df['PRODUCT_CORP'].str.split(' （').str[1].str.split('|').str[1]+'）'
        df['MOLECULE_TC'] = df['MOLECULE_TC'].str.split('|').str[1]

    if is_pivoted is True:
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

        return pivoted
    else:
        return df


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


def get_ptable(df, label):
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
    df_combined.columns = ['最新' + label,
                           '净增长',
                           '份额',
                           '份额同比变化',
                           '同比增长率',
                           'EI']

    return df_combined


def get_ptable_trend(df, label):
    # 准备绘图数据，根据不同图表样式将原始数微调
    df = df.iloc[[-17, -13, -9, -5, -1], :]

    df_share = df.transform(lambda x: x / x.sum(), axis=1)
    # df_share.dropna(how='all', inplace=True)

    df_share_diff = df_share.diff(periods=1)
    df_share_diff.drop(df_share_diff.index[0], inplace=True)
    # df_share_diff.dropna(how='all', inplace=True)

    df_gr = df.pct_change(periods=1)
    df_gr.drop(df_gr.index[0], inplace=True)
    df_gr.replace([np.inf, -np.inf], np.nan, inplace=True)

    df_cagr = (df.iloc[-1]/df.iloc[0])**0.25-1
    # df_gr.dropna(how='all', inplace=True)


    df.index = df.index.strftime("%Y-%m") + '\n' + label
    df_share.index = df_share.index.strftime("%Y-%m") + '\n' + '份额'
    df_share_diff.index = df_share_diff.index.strftime("%Y-%m") + '\n' + '份额Δ'
    df_gr.index = df_gr.index.strftime("%Y-%m") + '\n' + '同比增长'
    df_cagr.name = '4年CAGR'

    df_combined = pd.concat(
        [df.T, df_share.T, df_share_diff.T, df_gr.T, df_cagr], axis=1)

    return df_combined


def get_price(form_dict, volume_unit):
    form_dict_price = form_dict.copy()  # 一定要这么处理，字典直接=是引用对象而不是拷贝
    form_dict_price['UNIT_select'] = ['Value']
    df_value = get_df(form_dict_price)
    df_value = df_value.iloc[[-17, -13, -9, -5, -1], :]
    form_dict_price['UNIT_select'] = [volume_unit]
    df_volume = get_df(form_dict_price)
    df_volume = df_volume.iloc[[-17, -13, -9, -5, -1], :]

    df_value_latest = df_value.iloc[-1]

    df_price = df_value/df_volume

    df_price_gr = df_price.pct_change(periods=1)
    df_price_gr.drop(df_price_gr.index[0], inplace=True)
    df_price_gr.replace([np.inf, -np.inf], np.nan, inplace=True)

    df_price_cagr = (df_price.iloc[-1]/df_price.iloc[0])**0.25-1

    df_value_latest.name = '最新'+ form_dict['PERIOD_select'][0] + '金额'
    df_price.index = df_price.index.strftime("%Y-%m") + '\n' + form_dict['PERIOD_select'][0] + '单价'
    df_price_gr.index = df_price_gr.index.strftime("%Y-%m") + '\n' + '同比变化'
    df_price_cagr.name = '4年CAGR'

    df_combined = pd.concat(
        [df_value_latest, df_price.T, df_price_gr.T, df_price_cagr], axis=1, sort=False)

    return df_combined


def build_formatters_by_col(df):
    format_abs = lambda x: '{:,.0f}'.format(x)
    format_share = lambda x: '{:.1%}'.format(x)
    format_gr = lambda x: '{:.1%}'.format(x)
    format_currency = lambda x: '¥{:,.1f}'.format(x)
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


def prepare_chart(df,  # 输入经过pivoted方法透视过的df，不是原始df
                  chart_type,  # 图表类型字符串，人为设置，根据图表类型不同做不同的Pandas数据处理，及生成不同的Pyechart对象
                  form_dict,  # 前端表单字典，用来获得一些变量作为图表的标签如单位
                  ):
    SERIES_LIMIT = 10
    label = D_TRANS[form_dict['PERIOD_select'][0]] + D_TRANS[form_dict['UNIT_select'][0]]

    if chart_type == 'bar_total_trend':
        df_abs = df.sum(axis=1)  # Pandas列汇总，返回一个N行1列的series，每行是一个date的市场综合
        df_abs.index = df_abs.index.strftime("%Y-%m")  # 行索引日期数据变成2020-06的形式
        df_abs = df_abs.to_frame()  # series转换成df
        df_abs.columns = [label]  # 用一些设置变量为系列命名，准备作为图表标签
        df_gr = df_abs.pct_change(periods=4)  # 获取同比增长率
        df_gr.dropna(how='all', inplace=True)  # 删除没有同比增长率的行，也就是时间序列数据的最前面几行，他们没有同比
        df_gr.replace([np.inf, -np.inf, np.nan], '-', inplace=True)  # 所有分母为0或其他情况导致的inf和nan都转换为'-'
        chart = echarts_stackbar(df=df_abs,
                                 df_gr=df_gr
                                 )  # 调用stackbar方法生成Pyecharts图表对象
        return chart.dump_options()  # 用json格式返回Pyecharts图表对象的全局设置
    elif chart_type == 'stackarea_abs_trend':
        chart = echarts_stackarea(df.iloc[:, :SERIES_LIMIT], datatype='ABS')  # 直接使用绝对值时间序列
        return chart.dump_options()
    elif chart_type == 'stackarea_share_trend':
        df_share = df.transform(lambda x: x / x.sum(), axis=1)  # 时间序列转换为份额趋势
        df_share.replace([np.inf, -np.inf, np.nan], '-', inplace=True)  # 替换缺失值
        chart = echarts_stackarea100(df_share.iloc[:, :SERIES_LIMIT], datatype='SHARE')
        return chart.dump_options()
    elif chart_type == 'line_gr_trend':
        df_gr = df.pct_change(periods=4)  # 以4（同比）为间隔计算百分比增长
        df_gr.dropna(how='all', inplace=True)  # 删除因为没有分母而计算后变成na的前几个时序
        df_gr.replace([np.inf, -np.inf, np.nan], '-' , inplace=True)  # 替换正负无穷
        chart = echarts_line(df_gr.iloc[:, :SERIES_LIMIT], datatype='GR')
        return chart.dump_options()
    elif chart_type == 'bubble_performance':
        df_abs = df.iloc[-1, :]  # 获取最新时间粒度的绝对值
        df_share = df.transform(lambda x: x / x.sum(), axis=1).iloc[-1, :]  # 获取份额
        df_diff = df.diff(periods=4).iloc[-1, :]  # 获取同比净增长

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