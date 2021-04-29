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
from rdpac.models import *

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
    df = pd.read_excel("vbp.xlsx", sheet_name="第四轮集采", header=0)
    df = df.drop_duplicates("药品通用名")
    # pivoted = pd.pivot_table(df, index='药品通用名', values='最高限价', aggfunc=np.mean)
    # d = pivoted.to_dict()['最高限价']

    l = []
    for tender in df.values:
        print(tender)
        tender_begin = datetime.datetime.strptime("01-05-2021", "%d-%m-%Y")
        l.append(
            Tender(
                target=tender[1],
                vol="第四轮45品种",
                tender_begin=tender_begin,
                ceiling_price=tender[9],
            )
        )

    Tender.objects.bulk_create(l)


def import_volume():
    df = pd.read_excel("vbp_amount.xlsx", sheet_name="第四轮集采 by 省")
    # df = df[df["品种"] != "碳酸氢钠口服常释剂型"]
    print(df)

    l = []
    for volume in df.values:
        print(volume)
        l.append(
            Volume(
                tender=Tender.objects.get(target=volume[1]),
                region=volume[0],
                spec=volume[2],
                amount_reported=volume[3],
            )
        )

    Volume.objects.bulk_create(l)


def import_bid():
    df = pd.read_excel("vbp.xlsx", sheet_name="第四轮集采", header=0)
    df.fillna("-", inplace=True)
    print(df)

    tenders = Tender.objects.all()
    for tender in tenders:
        for bid in df.values:
            tender_name = bid[1]
            multi_spec = bid[2]
            spec = bid[3]
            company_full_name = bid[4]
            company_abbr_name = bid[5]
            origin = bid[6]
            mnc_or_local = bid[7]
            original_price = bid[10]
            bid_price = bid[11]
            region_win = bid[12]

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
                    )
                else:
                    bid_obj = Bid.objects.create(
                        tender=tender,
                        bidder=company,
                        origin=D_BOOLEAN[origin],
                        bid_spec=spec,
                        bid_price=bid_price,
                        original_price=original_price,
                    )

                if region_win != "-":
                    list_region = [x.strip() for x in region_win.split("，")]
                    for region in list_region:
                        volume_objs = Volume.objects.filter(
                            tender__target=tender_name, region=region,
                        )
                        for obj in volume_objs:
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
        l.append(
            Drug(
                molecule_cn=drug[6],
                molecule_en=drug[7],
                product_name_cn=drug[5],
                product_name_en=drug[4],
            )
        )

    Drug.objects.all().delete()
    Drug.objects.bulk_create(l)


def import_sales():
    df = pd.read_excel("rdpac.xlsx", sheet_name="summary", header=0)
    
    Sales.objects.all().delete()
    
    start_col = 15
    for sale in df.values:
        print(sale)
        for j in range(8):
            company = Company.objects.get(name_cn=sale[1])
            drug = Drug.objects.get(product_name_en=sale[4])
            
            if math.isnan(sale[start_col+j]) is False:
                sale_obj = Sales.objects.create(
                    company = company,
                    drug = drug,
                    year = df.columns[start_col+j],
                    netsales_value = sale[start_col+j]
                )
                
    # tenders = Tender.objects.all()
    # for tender in tenders:
    #     for bid in df.values:
    #         tender_name = bid[1]
    #         multi_spec = bid[2]
    #         spec = bid[3]
    #         company_full_name = bid[4]
    #         company_abbr_name = bid[5]
    #         origin = bid[6]
    #         mnc_or_local = bid[7]
    #         original_price = bid[10]
    #         bid_price = bid[11]
    #         region_win = bid[12]

    #         if tender_name == tender.target:
    #             if Company.objects.filter(full_name=company_full_name).exists():
    #                 company = Company.objects.get(full_name=company_full_name)
    #             else:
    #                 company = Company.objects.create(
    #                     full_name=company_full_name,
    #                     abbr_name=company_abbr_name,
    #                     mnc_or_local=D_BOOLEAN[mnc_or_local],
    #                 )
    #             if original_price == "-":
    #                 bid_obj = Bid.objects.create(
    #                     tender=tender,
    #                     bidder=company,
    #                     origin=D_BOOLEAN[origin],
    #                     bid_spec=spec,
    #                     bid_price=bid_price,
    #                 )
    #             else:
    #                 bid_obj = Bid.objects.create(
    #                     tender=tender,
    #                     bidder=company,
    #                     origin=D_BOOLEAN[origin],
    #                     bid_spec=spec,
    #                     bid_price=bid_price,
    #                     original_price=original_price,
    #                 )

    #             if region_win != "-":
    #                 list_region = [x.strip() for x in region_win.split("，")]
    #                 for region in list_region:
    #                     volume_objs = Volume.objects.filter(
    #                         tender__target=tender_name, region=region,
    #                     )
    #                     for obj in volume_objs:
    #                         obj.winner = bid_obj
    #                         obj.save()

        # l = []
        # for tender in tenders:
        #     l.append(Record(tender=tender, real_or_sim=True))

        # Record.objects.bulk_create(l)
        
        
if __name__ == "__main__":
    # importModel(D_MODEL)
    # import_tender()
    # import_volume()
    # import_bid()
    # update_tender()
    # import_company()
    import_drug()
    import_sales()
    print("Done!", time.process_time())
    # print(Drug.objects.get(pk=2248).product_name_cn)