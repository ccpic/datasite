from django.http import QueryDict
import pandas as pd
from typing import List, Union


# 根据数字返回动态颜色的Semantic UI label标签
def html_label(text: Union[str,int, float]) -> str:
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
        "社区医院":"green",
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
                statement = statement + "'" + data + "', "
            statement = statement[:-2]
        else:
            statement = "'" + selected + "'"
        if statement != "":
            sql = sql + operator + field_name + " in (" + statement + ")"
    return sql


def format_numbers(num_str: str, format_str: str) -> str:
    try:
        num_str = format_str.format(num_str)
    except ValueError:
        pass
    return num_str


def get_distinct_list(column: str, db_table: str, engine: str) -> list:
    sql = "Select DISTINCT " + column + " From " + db_table
    df = pd.read_sql_query(sql, engine)
    df.dropna(inplace=True)
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


def format_table(df: pd.DataFrame, id: str) -> str:
    formatters = build_formatters_by_col(df=df, table_id=id)

    table_formatted = df.to_html(
        escape=False,
        formatters=formatters,  # 逐列调整表格内数字格式
        classes="ui selectable celled table",  # 指定表格css class为Semantic UI主题
        table_id=id,  # 指定表格id
    )
    return table_formatted
