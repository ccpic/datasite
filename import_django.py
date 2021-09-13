#!/usr/bin/env python
import os
import time
from sqlalchemy import create_engine
import pandas as pd
import django
import datetime
import math
import numpy as np

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datasite.settings")
django.setup()

from chpa_data.views import *
from vbp.models import *

# from rdpac.models import *

engine = create_engine("mssql+pymssql://(local)/CHPA_1806")
table = "data"

D_BOOLEAN = {"是": True, "否": False}


def importModel(dict):
    for key in dict:
        sql = "SELECT Distinct " + key + " FROM " + table
        df = pd.read_sql(sql=sql, con=engine)
        df.dropna(inplace=True)
        print(df)
        l = []
        for item in df.values:
            l.append(dict[key](name=item[0]))

        dict[key].objects.all().delete()
        dict[key].objects.bulk_create(l)


"""以下部分为vbp导入模块"""


def import_tender():
    D_DATE = {
        "第二轮33品种": "01-04-2020",
        "第三轮56品种": "01-11-2020",
        "第四轮45品种": "01-05-2021",
        "第五轮62品种": "01-10-2021",
        "第一轮25品种扩围联盟地区": "01-12-2019",
    }
    df = pd.read_excel("vbp_summary_7.6.xlsx", sheet_name="汇总", header=0)
    df = df.drop_duplicates("药品通用名")
    # pivoted = pd.pivot_table(df, index='药品通用名', values='最高限价', aggfunc=np.mean)
    # d = pivoted.to_dict()['最高限价']

    l = []
    for tender in df.values:
        print(tender)
        tender_begin = datetime.datetime.strptime(D_DATE[tender[0]], "%d-%m-%Y")
        l.append(
            Tender(
                target=tender[2],
                vol=tender[0],
                tender_begin=tender_begin,
                # ceiling_price=tender[10],
                only_valid_spec=D_BOOLEAN[tender[16]],
            )
        )

    Tender.objects.bulk_create(l)


def import_volume():
    df = pd.read_excel("vbp_amount_7.6.xlsx", sheet_name="汇总")
    # df = df[df["品种"] != "碳酸氢钠口服常释剂型"]
    print(df)

    l = []
    for volume in df.values:
        print(volume)
        l.append(
            Volume(
                tender=Tender.objects.get(target=volume[2]),
                region=volume[1],
                spec=volume[3],
                amount_reported=volume[4],
            )
        )

    Volume.objects.bulk_create(l)


def import_bid():

    D_DELTA = {
        "埃索美拉唑(艾司奥美拉唑)注射剂": {
            "重庆莱美": ["40mg"],
            "特瑞药业": ["40mg"],
            "海思科制药": ["20mg", "40mg"],
            "海南中玉": ["20mg", "40mg"],
            "海南倍特": ["40mg"],
            "正大天晴": ["20mg", "40mg"],
            "扬子江药业": ["40mg"],
            "山东裕欣": ["40mg"],
            "江苏奥赛康": ["20mg", "40mg"],
            "福安药业": ["40mg"],
        },
        "单硝酸异山梨酯缓释控释剂型": {
            "乐普医疗": ["40mg"],
            "合肥合源": ["50mg"],
            "珠海润都": ["40mg"],
            "齐鲁制药": ["40mg"],
            "鲁南制药": ["40mg"],
        },
        "碘海醇注射剂 100ml:30g(I)": {
            "通用电气": ["100ml:30g(I)"],
            "上海司太立": ["100ml:30g(I)"],
            "扬子江药业": ["100ml:30g(I)"],
        },
        "碘海醇注射剂 100ml:35g(I)": {
            "通用电气": ["100ml:35g(I)"],
            "上海司太立": ["100ml:35g(I)"],
            "北京北陆": ["100ml:35g(I)"],
        },
        "碘克沙醇注射剂": {
            "通用电气": ["100ml:32g(I)"],
            "上海司太立": ["100ml:32g(I)"],
            "正大天晴": ["100ml:32g(I)"],
            "扬子江药业": ["100ml:32g(I)"],
        },
        "脂肪乳氨基酸葡萄糖注射剂": {"海思科制药": ["1440ml"], "科伦药业": ["1440ml"], "费森": ["1440ml"],},
        "中/长链脂肪乳(C8-24Ve)注射剂": {
            "科伦药业": ["250ml(20%)"],
            "广东嘉博": ["250ml(20%)"],
            "德国贝朗": ["250ml(20%)"],
        },
    }

    df = pd.read_excel("vbp_summary_7.6.xlsx", sheet_name="汇总", header=0)
    df.fillna("-", inplace=True)
    print(df)

    tenders = Tender.objects.all()
    for tender in tenders:
        for bid in df.values:
            tender_name = bid[2]
            multi_spec = bid[3]
            spec = bid[4]
            company_full_name = bid[5]
            company_abbr_name = bid[6]
            origin = bid[7]
            mnc_or_local = bid[8]
            ceiling_price = bid[10]
            original_price = bid[11]
            bid_price = bid[12]
            region_win = bid[13]

            if tender_name == tender.target:
                if Company.objects.filter(full_name=company_full_name).exists():
                    company = Company.objects.get(full_name=company_full_name)
                else:
                    company = Company.objects.create(
                        full_name=company_full_name,
                        abbr_name=company_abbr_name,
                        mnc_or_local=D_BOOLEAN[mnc_or_local],
                    )
                if original_price == "-":
                    bid_obj = Bid.objects.create(
                        tender=tender,
                        bidder=company,
                        origin=D_BOOLEAN[origin],
                        bid_spec=spec,
                        bid_price=bid_price,
                        ceiling_price=ceiling_price,
                    )
                else:
                    bid_obj = Bid.objects.create(
                        tender=tender,
                        bidder=company,
                        origin=D_BOOLEAN[origin],
                        bid_spec=spec,
                        bid_price=bid_price,
                        original_price=original_price,
                        ceiling_price=ceiling_price,
                    )
                # 将对应区域销量和中标者挂钩
                if region_win != "-":
                    list_region = [x.strip() for x in region_win.split(",")]
                    for region in list_region:
                        volume_objs = Volume.objects.filter(
                            tender__target=tender_name, region=region,
                        )
                        for obj in volume_objs:
                            if tender.target in D_DELTA:  # 处理第五轮的特殊规则，带三角标志的标的
                                if bid_obj.bidder.abbr_name in D_DELTA[tender.target]:
                                    if (
                                        obj.spec
                                        in D_DELTA[tender.target][
                                            bid_obj.bidder.abbr_name
                                        ]
                                    ):
                                        obj.winner = bid_obj
                                        obj.save()
                            else:
                                obj.winner = bid_obj
                                obj.save()
    # l = []
    # for tender in tenders:
    #     l.append(Record(tender=tender, real_or_sim=True))

    # Record.objects.bulk_create(l)


def update_tender():
    tenders = Tender.objects.all()
    tender_begin = datetime.datetime.strptime("01-11-2020", "%d-%m-%Y")
    for tender in tenders:
        if tender.vol == "第三轮56品种":
            tender.tender_begin = tender_begin
            tender.save()
            print(tender_begin)


"""以下部分为rdpac导入模块"""


def import_company():
    df = pd.read_excel("rdpac.xlsx", sheet_name="summary", header=0)
    df = df.drop_duplicates("Company Name_CN")
    # pivoted = pd.pivot_table(df, index='药品通用名', values='最高限价', aggfunc=np.mean)
    # d = pivoted.to_dict()['最高限价']

    l = []
    for company in df.values:
        print(company)
        l.append(
            Company(
                name_cn=company[1],
                name_en=company[2],
                abbr=company[0],
                country_code=company[3],
            )
        )

    Company.objects.all().delete()
    Company.objects.bulk_create(l)


def import_drug():
    df = pd.read_excel("rdpac.xlsx", sheet_name="summary", header=0)
    df.fillna("", inplace=True)
    df = df.drop_duplicates("Product Name-RDPAC")

    l = []
    for drug in df.values:
        print(drug)
        tc_iii = TC_III.objects.get(code=drug[10])
        l.append(
            Drug(
                molecule_cn=drug[7],
                molecule_en=drug[8],
                product_name_cn=drug[5],
                product_name_en=drug[4],
                tc_iii=tc_iii,
            )
        )

    Drug.objects.all().delete()
    Drug.objects.bulk_create(l)


def import_sales():
    df = pd.read_excel("rdpac.xlsx", sheet_name="summary", header=0)

    Sales.objects.all().delete()

    start_col = 16
    for sale in df.values:
        print(sale)
        for j in range(8):
            company = Company.objects.get(name_cn=sale[1])
            drug = Drug.objects.get(product_name_en=sale[4])

            if math.isnan(sale[start_col + j]) is False:
                sale_obj = Sales.objects.create(
                    company=company,
                    drug=drug,
                    year=df.columns[start_col + j],
                    netsales_value=sale[start_col + j],
                )


def import_tc():
    sql = "SELECT DISTINCT [TC I], [TC II], [TC III] FROM " + table
    df = pd.read_sql(sql=sql, con=engine)
    df.dropna(inplace=True)
    tc_i = df["TC I"].unique()

    l = []
    for desc in tc_i:
        print(desc[0], desc[1:].split("|")[0], desc[1:].split("|")[1])

        l.append(
            TC_I(
                code=desc[0],
                name_en=desc[1:].split("|")[0],
                name_cn=desc[1:].split("|")[1],
            )
        )

    TC_I.objects.all().delete()
    TC_I.objects.bulk_create(l)

    tc_ii = df["TC II"].unique()
    l = []
    for desc in tc_ii:
        print(desc[:3], desc[3:].split("|")[0], desc[3:].split("|")[1])
        tc_i = TC_I.objects.get(code=desc[0])
        l.append(
            TC_II(
                code=desc[:3],
                name_en=desc[3:].split("|")[0],
                name_cn=desc[3:].split("|")[1],
                tc_i=tc_i,
            )
        )

    TC_II.objects.all().delete()
    TC_II.objects.bulk_create(l)

    tc_iii = df["TC III"].unique()
    l = []
    for desc in tc_iii:
        print(desc[:5], desc[5:].split("|")[0], desc[5:].split("|")[1])
        tc_ii = TC_II.objects.get(code=desc[:3])
        l.append(
            TC_III(
                code=desc[:5],
                name_en=desc[5:].split("|")[0],
                name_cn=desc[5:].split("|")[1],
                tc_ii=tc_ii,
            )
        )

    TC_III.objects.all().delete()
    TC_III.objects.bulk_create(l)


if __name__ == "__main__":
    importModel(D_MODEL)
    # import_tender()
    # import_volume()
    # import_bid()
    # update_tender()
    # import_company()
    # import_drug()
    # import_sales()
    # import_tc()
    print("Done!", time.process_time())
    # print(Drug.objects.get(pk=2248).product_name_cn)
