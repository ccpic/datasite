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
from vbp.models import Company, Tender, Volume, Bid
from rdpac.models import Drug, Sales

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


def import_tender(vol: str):
    D_DATE = {
        "第二轮33品种": "01-04-2020",
        "第三轮56品种": "01-11-2020",
        "第四轮45品种": "01-05-2021",
        "第五轮62品种": "01-10-2021",
        "第七轮61品种": "01-11-2022",
        "第八轮40品种": "01-07-2023",
        "第九轮42品种": "01-03-2024",
        "第一轮25品种扩围联盟地区": "01-12-2019",
    }
    df = pd.read_excel("vbp_summary_2023.11.29.xlsx", sheet_name="汇总", header=0)
    mask = df["批次"] == vol
    df = df.loc[mask, :]
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


def import_volume(vol: str):
    df = pd.read_excel("vbp_amount_2023.11.29.xlsx", sheet_name="汇总")
    mask = df["批次"] == vol
    df = df.loc[mask, :]
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


def import_bid(vol: str):
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
        "脂肪乳氨基酸葡萄糖注射剂": {
            "海思科制药": ["1440ml"],
            "科伦药业": ["1440ml"],
            "费森": ["1440ml"],
        },
        "中/长链脂肪乳(C8-24Ve)注射剂": {
            "科伦药业": ["250ml(20%)"],
            "广东嘉博": ["250ml(20%)"],
            "德国贝朗": ["250ml(20%)"],
        },
        "碘帕醇注射剂": {
            "北京北陆": ["100ml:37g(I)"],
            "博莱科信谊": ["100ml:37g(I)"],
            "上海司太立": ["100ml:37g(I)"],
            "正大天晴": ["100ml:37g(I)"],
        },
        "替罗非班注射剂型": {
            "科伦药业": ["100ml:盐酸替罗非班5mg与氯化钠0.9g"],
            "西安万隆": ["100ml:盐酸替罗非班5mg与氯化钠0.9g"],
            "赤峰源生": ["250ml:盐酸替罗非班12.5mg与氯化钠2.25g"],
            "四川美大康": ["100ml:盐酸替罗非班5mg与氯化钠0.9g"],
            "鲁南制药": ["100ml:盐酸替罗非班5mg与氯化钠0.9g"],
            "石药集团": ["100ml:盐酸替罗非班5mg与氯化钠0.9g"],
        },
        "盐酸美金刚缓释胶囊": {
            "宜昌人福": ["7mg"],
            "成都苑东生物": ["7mg"],
            "浙江京新": ["7mg"],
            "天津天士力": ["7mg"],
            "青岛百洋": ["7mg"],
            "江苏长泰": ["28mg"],
        },
        "甲泼尼龙口服常释剂型": {
            "浙江仙琚": ["16mg"],
            "天津天药": ["4mg"],
            "山东新华鲁抗": ["4mg"],
        },
        "头孢米诺注射剂": {
            "齐鲁安替": ["1g"],
            "四川合信": ["0.25g"],
            "山东润泽": ["0.5g"],
            "上海欣峰": ["1g"],
            "海南海灵": ["1g"],
            "北大医药": ["1g"],
        },
        "氨氯地平阿托伐他汀口服常释剂型": {
            "福建海西": ["5mg/10mg(以氨氯地平/阿托伐他汀计)"],
            "正大天晴": ["5mg/10mg(以氨氯地平/阿托伐他汀计)"],
            "华润赛科": ["5mg/10mg(以氨氯地平/阿托伐他汀计)"],
            "北京嘉林": ["5mg/10mg(以氨氯地平/阿托伐他汀计)"],
        },
        "氯沙坦氢氯噻嗪口服常释剂型": {
            "浙江华海": ["氯沙坦钾50mg和氢氯噻嗪12.5mg"],
            "乐普医疗": ["氯沙坦钾50mg和氢氯噻嗪12.5mg", "氯沙坦钾100mg和氢氯噻嗪25mg"],
            "浙江诺得": ["氯沙坦钾100mg和氢氯噻嗪25mg"],
            "苏州东瑞": ["氯沙坦钾50mg和氢氯噻嗪12.5mg"],
        },
        "阿莫西林克拉维酸口服常释剂型": {
            "鲁南制药": ["0.375g(2:1)"],
            "湘北威尔曼": ["1g(7:1)"],
            "瑞阳制药": ["0.375g(2:1)"],
            "石药集团": ["0.375g(2:1)"],
            "华北制药": ["0.375g(2:1)"],
        },
        "头孢哌酮舒巴坦注射剂": {
            "苏州东瑞": ["1g(1:1)"],
            "齐鲁安替": ["1g(1:1)", "2g(1:1)"],
            "广东金城金素": ["1g(1:1)", "1.5g(1:1)", "2g(1:1)"],
            "山东润泽": ["1g(1:1)", "2g(1:1)"],
            "成都倍特": ["1g(1:1)", "2g(1:1)"],
            "科伦药业": ["1g(1:1)", "2g(1:1)"],
            "深圳立健": ["1g(1:1)", "2g(1:1)"],
            "海南合瑞": ["1g(1:1)"],
            "福安药业": ["1g(1:1)", "1.5g(1:1)", "2g(1:1)"],
            "苏州二叶": ["1g(1:1)", "2g(1:1)", "3g(1:1)"],
        },
        "骨化三醇口服常释剂型": {
            "四川国为": ["0.25μg", "0.5μg"],
            "正大制药": ["0.25μg", "0.5μg"],
            "南京海融": ["0.5μg"],
            "河南泰丰": ["0.25μg", "0.5μg"],
        },
        "奥美拉唑碳酸氢钠口服常释剂型": {
            "鲁南制药": ["奥美拉唑20mg与碳酸氢钠1100mg", "奥美拉唑40mg与碳酸氢钠1100mg"],
            "厦门恩成": ["奥美拉唑20mg与碳酸氢钠1100mg"],
            "浙江花园药业": ["奥美拉唑20mg与碳酸氢钠1100mg", "奥美拉唑40mg与碳酸氢钠1100mg"],
            "北京百奥": ["奥美拉唑20mg与碳酸氢钠1100mg", "奥美拉唑40mg与碳酸氢钠1100mg"],
            "重庆华森": ["奥美拉唑20mg与碳酸氢钠1100mg"],
        },
        "奥美沙坦酯氨氯地平口服常释剂型": {
            "国药集团": ["每片含奥美沙坦酯20mg和苯磺酸氨氯地平5mg（以氨氯地平计）"],
            "安庆回音": ["每片含奥美沙坦酯20mg和苯磺酸氨氯地平5mg（以氨氯地平计）"],
            "江苏诺泰澳赛诺": ["每片含奥美沙坦酯20mg和苯磺酸氨氯地平5mg（以氨氯地平计）"],
            "江苏万高": ["每片含奥美沙坦酯20mg和苯磺酸氨氯地平5mg（以氨氯地平计）"],
            "扬子江药业": ["每片含奥美沙坦酯20mg和苯磺酸氨氯地平5mg（以氨氯地平计）"],
            "重庆华森": ["每片含奥美沙坦酯20mg和苯磺酸氨氯地平5mg（以氨氯地平计）"],
            "正大天晴": ["每片含奥美沙坦酯20mg和苯磺酸氨氯地平5mg（以氨氯地平计）"],
            "奥罗宾多": [
                "每片含奥美沙坦酯20mg和苯磺酸氨氯地平5mg（以氨氯地平计）",
                "每片含奥美沙坦酯40mg和苯磺酸氨氯地平5mg（以氨氯地平计）",
                "每片含奥美沙坦酯40mg和苯磺酸氨氯地平10mg（以氨氯地平计）",
            ],
        },
        "奥美沙坦酯氢氯噻嗪口服常释剂型": {
            "宁波美舒": ["每片含奥美沙坦酯20mg与氢氯噻嗪12.5mg"],
            "江苏万高": ["每片含奥美沙坦酯20mg与氢氯噻嗪12.5mg"],
            "浙江华海": ["每片含奥美沙坦酯20mg与氢氯噻嗪12.5mg", "每片含奥美沙坦酯40mg与氢氯噻嗪12.5mg"],
            "上海现代": ["每片含奥美沙坦酯20mg与氢氯噻嗪12.5mg"],
            "华润赛科": ["每片含奥美沙坦酯20mg与氢氯噻嗪12.5mg"],
            "北京元延": ["每片含奥美沙坦酯20mg与氢氯噻嗪12.5mg"],
            "浙江诺得": ["每片含奥美沙坦酯20mg与氢氯噻嗪12.5mg"],
        },
        "硫酸镁注射剂型": {
            "天津金耀": ["2ml:1g", "10ml:5g", "20ml:10g"],
            "石家庄凯达": ["10ml:5g", "20ml:10g"],
            "扬州中宝": ["10ml:5g", "20ml:10g"],
            "科伦药业": ["10ml:5g", "20ml:10g"],
            "上海禾丰": ["2ml:1g", "10ml:5g", "20ml:10g"],
            "江苏华阳": ["10ml:5g", "20ml:10g"],
            "海南倍特": ["2ml:1g", "10ml:5g", "20ml:10g"],
        },
        "帕罗西汀肠溶缓释片": {
            "北京福元": ["12.5mg", "25mg", "37.5mg"],
            "华益泰康": ["37.5mg"],
            "上海宣泰": ["25mg", "37.5mg"],
            "深圳信立泰": ["12.5mg", "25mg", "37.5mg"],
        },
        "卡泊芬净注射剂": {
            "广州一品红": ["50mg"],
            "江苏恒瑞": ["50mg"],
            "正大天晴": ["50mg", "70mg"],
            "海思科制药": ["50mg"],
            "齐鲁制药": ["50mg"],
            "海南海灵": ["50mg"],
        },
        "雷贝拉唑口服常释剂型": {
            "珠海润都": ["20mg"],
            "重庆药友": ["20mg"],
            "晋城海斯": ["20mg"],
            "山东新华": ["10mg", "20mg"],
            "上海安必生": ["20mg"],
            "湖南九典": ["10mg", "20mg"],
            "江西山香": ["10mg", "20mg"],
            "济川药业": ["20mg"],
        },
    }

    df = pd.read_excel("vbp_summary_2023.11.29.xlsx", sheet_name="汇总", header=0)
    mask = df["批次"] == vol
    df = df.loc[mask, :]
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
                            tender__target=tender_name,
                            region=region,
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
    # importModel(D_MODEL)
    import_tender("第九轮42品种")
    import_volume("第九批集采")
    import_bid("第九轮42品种")

    # update_tender()

    # import_company()
    # import_drug()
    # import_sales()
    # import_tc()
    print("Done!", time.process_time())
    # print(Drug.objects.get(pk=2248).product_name_cn)
