import requests
import json
from hyper.contrib import HTTP20Adapter
import re
import pandas as pd
from sqlalchemy import create_engine, engine
import sqlalchemy.types as t
import numpy as np
import datetime


URL = "https://api.m.jd.com/client.action?functionId=getRankLanding&appid=JDReactRankingList&body=%7B%22version%22%3A%22109%22%2C%22rankType%22%3A10%2C%22source%22%3A%22dacu%22%2C%22rankId%22%3A%22171523%22%2C%22extraParam%22%3A%7B%7D%2C%22fromName%22%3A%22main_channel%22%2C%22hasVenderRank%22%3A%221%22%7D&clientVersion=9.4.2&client=wh5&uuid=16124227073121239123718&area=1_2802_54747_0&pin=zldGuWUptmM&jsonp=jsonp_1656037379675_6571"

PAYLOAD = {
    "body": {
        "version": "109",
        "rankType": 10,
        "source": "dacu",
        "rankId": "171523",
        "extraParam": {},
        "fromName": "main_channel",
        "hasVenderRank": "1",
    }
}


def getHeaders():
    headers = {
        "authority": "api.m.jd.com",
        "method": "GET",
        "path": "/client.action?functionId=getRankLanding&appid=JDReactRankingList&body=%7B%22version%22%3A%22109%22%2C%22rankType%22%3A10%2C%22source%22%3A%22dacu%22%2C%22rankId%22%3A%22171523%22%2C%22extraParam%22%3A%7B%7D%2C%22fromName%22%3A%22main_channel%22%2C%22hasVenderRank%22%3A%221%22%7D&clientVersion=9.4.2&client=wh5&uuid=16124227073121239123718&area=1_2802_54747_0&pin=zldGuWUptmM&jsonp=jsonp_1656037379675_6571",
        "scheme": "https",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest",
        "referer": "https://ranking.m.jd.com/comLandingPage/comLandingPage?contentId=171523&rankType=10&fromName=main_channel&sku=&preSrc=undefined&hideAd=xxx&ptag=",
    }
    return headers


def parse_jsonp(jsonp_str: str):
    try:
        return re.search("^[^(]*?\((.*)\)[^)]*$", jsonp_str).group(1)
    except:
        raise ValueError("Invalid JSONP")


def parse_df(url: str, payload: dict):
    sessions = requests.session()
    sessions.mount("api.m.jd.com", HTTP20Adapter())
    r = sessions.get(url, data=payload, headers=getHeaders())
    print(r.text)
    j = json.loads(parse_jsonp(r.text))["result"]["products"]
    df = pd.DataFrame.from_dict(j)
    df.to_csv("test.csv",encoding="utf-8-sig")
    df = df.loc[
        :,
        [
            "skuId",  # SKU ID
            "jdPrice",  # 价格
            "lowestDay",  # 最低价天数
            "rankNum",  # 销量排名
            "title",  # 产品标题
            "threeCategory",  # 品类 ID
            "shopId",  # 店铺 ID
            "soldRate",  # 未知参数，先记录
            "img",  # 封面主图Url
            "imageUrl",  # 产品图Url
            "secKill",  # 当前是否有秒杀活动
            # "sellPoints",  # 卖点
            # "shorttext",  # 推广字样
            "buyedStr",  # 多少万人买过
            "saleInfoStr",  # 过去24小时售出
        ],
    ]
    df["PRODUCT"] = df["title"].apply(lambda x: x.split(" ")[0])  # 从title字段提取产品名
    df["DATETIME"] = datetime.datetime.now()
    df["buyedStr"] = df["buyedStr"].apply(lambda x: float(x[:-4]))  # 从buyedStr字段提取购买人次
    df["saleInfoStr"] = df["saleInfoStr"].apply(lambda x: int(x[6:][:-1]))
    df.columns = [
        "SKU_ID",
        "PRICE",
        "LOWEST_DAYS",
        "RANK",
        "TITLE",
        "CATEGORY",
        "SHOP_ID",
        "SOLD_RATE",
        "IMG_PROMOTION",
        "IMG_PRODUCT",
        "SEC_KILL",
        # "SELL_POINTS",
        # "SHORT_TEXTS",
        "BUYED_TIMES",
        "SALES_24H",
        "PRODUCT",
        "DATETIME",
    ]
    return df


def import_data(
    df: pd.DataFrame, engine: engine, table: str,
):
    print("start importing...")
    df.replace([np.inf, -np.inf], np.nan, inplace=True)  # 因分母为0除法产生的inf和-inf替换成nan

    df.to_sql(
        table,
        con=engine,
        if_exists="append",
        index=False,
        dtype={
            "SKU_ID": t.NVARCHAR(length=12),
            "PRICE": t.FLOAT,
            "LOWEST_DAYS": t.INTEGER,
            "RANK": t.INTEGER,
            "TITLE": t.NVARCHAR(length=100),
            "CATEGORY": t.NVARCHAR(length=5),
            "SHOP_ID": t.NVARCHAR(length=10),
            "SOLD_RATE": t.INTEGER,
            "IMG_PROMOTION": t.NVARCHAR(length=200),
            "IMG_PRODUCT": t.NVARCHAR(length=200),
            "SEC_KILL": t.Boolean,
            # "SELL_POINTS": t.NVARCHAR(length=100),
            # "SHORT_TEXTS": t.NVARCHAR(length=100),
            "BUYED_TIMES": t.FLOAT,
            "SALES_24H": t.INTEGER,
            "PRODUCT": t.NVARCHAR(length=100),
            "DATETIME": t.DATETIME,
        },
    )


if __name__ == "__main__":
    engine = create_engine("mssql+pymssql://(local)/eCom")  # 本地数据库
    # engine = create_engine("mssql+pymssql://sa:Luna1117@49.232.203.83/eCom") # 远程数据库
    table = "jd_cv_rank"
    df = parse_df(url=URL, payload=PAYLOAD)
    print(df)
    import_data(df, engine, table)
