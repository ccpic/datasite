from django.http import QueryDict
import pandas as pd
from typing import List, Union
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import numpy as np
import math
import json
from dateutil.relativedelta import relativedelta
import datetime

# 根据指定相对时间段提取dataframe的索引tuple
def date_mask(df: pd.DataFrame, date: datetime.datetime, period: str):
    date_ya = date.replace(year=date.year - 1)  # 同比月份
    date_year_begin = date.replace(month=1)  # 本年度开头
    date_ya_begin = date_ya.replace(month=1)  # 去年开头
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


# 解决json dump numpy相关格式报错的问题
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


# 根据前端Datatables返回的aodata对原始df处理并分页
def get_dt_page(df: pd.DataFrame, aodata: dict, dict_order: dict) -> Paginator.page:
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

    # 根据用户权限，前端参数，搜索关键字filter df
    mask = np.column_stack(
        [df[col].astype(str).str.contains(search_key, na=False) for col in df]
    )
    df = df.loc[mask.any(axis=1)]

    # 排序
    df = df.sort_values(
        by=dict_order[sort_column], ascending=True if sort_order == "asc" else False
    )

    # 对list进行分页
    paginator = Paginator(df.to_dict("records"), length)
    # 把数据分成10个一页。
    try:
        page = paginator.page(start / length + 1)
    # 请求页数错误
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    return page


# 根据数字返回动态颜色的Semantic UI label标签
def html_label(text: Union[str, int, float]) -> str:
    COLOR_DICT = {
        "10": "red",
        "9": "orange",
        "8": "yellow",
        "7": "olive",
        "6": "green",
        "5": "teal",
        "4": "blue",
        "3": "violet",
        "2": "purple",
        "1": "brown",
        "等级医院": "blue",
        "社区医院": "olive",
        "目标": "green",
        "非目标": "red",
    }
    color = COLOR_DICT.get(str(text), "black")
    html_str = '<div class="ui %s basic label">%s</div>' % (color, text)
    return html_str


def qdict_to_dict(qdict: QueryDict) -> dict:
    """Convert a Django QueryDict to a Python dict.

    Single-value fields are put in directly, and for multi-value fields, a list
    of all values is stored at the field's key.

    """
    return {k: v[0] if len(v) == 1 else v for k, v in qdict.lists()}


def sql_extent(
    sql: str, field_name: str, selected: Union[List[str], str], operator: str = " AND "
) -> str:
    if selected is not None:
        statement = ""
        if isinstance(selected, list):
            for data in selected:
                statement = statement + f"'{data}', "
            statement = statement[:-2]  # 去除最后一个循环产生的", "
        else:
            statement = f"'{selected }'"
        if statement != "":
            sql = f"{sql}{operator}{field_name} in ({statement})"
    return sql


def format_numbers(
    num_str: str, format_str: str, else_str: Union[str, None] = None, ignore_nan=False,
) -> str:
    if ignore_nan and math.isnan(float(num_str)):
        if else_str is not None:
            num_str = else_str
    else:
        try:
            num_str = format_str.format(num_str)
        except ValueError:
            pass
            if else_str is not None:
                num_str = else_str
    return num_str


def get_distinct_list(column: str, db_table: str, engine: str) -> list:
    sql = f"Select DISTINCT {column} From {db_table}"
    df = pd.read_sql_query(sql, engine)
    df.dropna(inplace=True)
    df.sort_values(by=column, inplace=True)
    l = df.values.flatten().tolist()
    return l


def build_formatters_by_col(df: pd.DataFrame, table_id: str = None) -> dict:
    format_abs = lambda x: format_numbers(x, "{:,.0f}")
    format_share = lambda x: format_numbers(x, "{:.1%}")
    format_gr = lambda x: format_numbers(x, "{:+.1%}")
    format_currency = lambda x: format_numbers(x, "¥{:,.1f}")

    d = {}
    if table_id == "ptable_comm_ratio_monthly":
        for column in df.columns:
            d[column] = format_share
    else:
        for column in df.columns:
            if any(x in str(column) for x in ["同比增长", "增长率", "CAGR", "同比变化"]):
                d[column] = format_gr
            elif any(
                x in str(column) for x in ["份额", "贡献", "达成", "占比", "覆盖率", "DOT %"]
            ):
                d[column] = format_share
            elif any(x in str(column) for x in ["价格", "单价"]):
                d[column] = format_currency
            elif "趋势" in str(column):
                d[column] = None
            else:
                d[column] = format_abs

    return d


def format_table(df: pd.DataFrame, id: str) -> str:
    formatters = build_formatters_by_col(df=df, table_id=id)

    table_formatted = df.to_html(
        escape=False,
        formatters=formatters,  # 逐列调整表格内数字格式
        classes="ui selectable celled table",  # 指定表格css class为Semantic UI主题
        table_id=id,  # 指定表格id
    )
    return table_formatted
