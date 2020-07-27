#!/usr/bin/env python
import os
import time
from sqlalchemy import  create_engine
import pandas as pd
import django
import datetime
import math

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datasite.settings")
django.setup()

from chpa_data.models import *
from vbp.models import *

engine = create_engine('mssql+pymssql://(local)/CHPA_1806')
table = 'data'

D_BOOLEAN = {
    '是': True,
    '否': False
}

def import_tender():
    df = pd.read_excel('vbp.xlsx', sheet_name='第二批集采', header=2)
    pivoted = pd.pivot_table(df, index='药品通用名', values='供应省份', aggfunc=len)
    d = pivoted.to_dict()['供应省份']

    l = []
    for key,value in d.items():
        print(key, value)
        tender_begin = datetime.datetime.strptime('10-03-2020', "%d-%m-%Y")
        l.append(Tender(target=key, vol='第二轮33品种', tender_begin=tender_begin, bidder_num=value))

    Tender.objects.bulk_create(l)


def import_volume():
    df = pd.read_excel('vbp_amount.xlsx', sheet_name='第二轮集采 by 省')
    df = df[df['品种']!='碳酸氢钠口服常释剂型']
    print(df)

    l = []
    for volume in df.values:
        print(volume)
        l.append(Volume(tender=Tender.objects.get(target=volume[1]), region=volume[0], spec=volume[2], amount_contract=volume[3]))

    Volume.objects.bulk_create(l)


def import_bid():
    df = pd.read_excel('vbp.xlsx', sheet_name='第二批集采', header=2)
    df.fillna('-', inplace=True)
    print(df)

    tenders = Tender.objects.all()
    for tender in tenders:
        for bid in df.values:
            tender_name = bid[1]
            multi_spec = bid[2]
            spec = bid[3]
            company_name = bid[4]
            origin = bid[5]
            mnc_or_local = bid[6]
            original_price = bid[8]
            bid_price = bid[9]
            region_win = bid[10]

            if tender_name == tender.target:
                if Company.objects.filter(name=company_name).exists():
                    company = Company.objects.get(name=company_name)
                else:
                    company = Company.objects.create(name=company_name,
                                                     mnc_or_local=D_BOOLEAN[mnc_or_local]
                                                 )
                if original_price == '-':
                    bid_obj=Bid.objects.create(tender=tender,
                                       bidder=company,
                                       origin=D_BOOLEAN[origin],
                                       bid_price=bid_price
                                       )
                else:
                    bid_obj=Bid.objects.create(tender=tender,
                                       bidder=company,
                                       origin=D_BOOLEAN[origin],
                                       bid_price=bid_price,
                                       original_price=original_price
                                       )

                if region_win != '-':
                    list_region = [x.strip() for x in region_win.split('，')]
                    for region in list_region:
                        print(tender_name, region, spec)
                        volume_objs=Volume.objects.filter(tender__target=tender_name,
                                                      region=region,
                                                      )
                        for obj in volume_objs:
                            obj.winner = bid_obj
                            obj.save()

        # l = []
        # for tender in tenders:
        #     l.append(Record(tender=tender, real_or_sim=True))

        # Record.objects.bulk_create(l)


def importModel(dict):
    for key in dict:
        sql = "SELECT Distinct [" + key + "] FROM "+table
        df = pd.read_sql(sql=sql, con=engine)
        df.dropna(inplace=True)
        print(df)
        l = []
        for item in df.values:
            l.append(dict[key](name=item[0]))

        dict[key].objects.bulk_create(l)


if __name__ == "__main__":
    # importModel(d_model)
    import_tender()
    import_volume()
    import_bid()
    print('Done!', time.process_time())