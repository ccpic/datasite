#!/usr/bin/env python
import os
import time
import pandas as pd
import django
import datetime
import numpy as np

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datasite.settings")
django.setup()

D_BOOLEAN = {"是": True, "否": False}


def import_nego():
    from nrdl_price.models import TC1, TC2, TC3, TC4, Subject, Negotiation

    df = pd.read_excel("医保谈判品种价格汇总-2017-2023-V2.xlsx")
    print(df)
    Negotiation.objects.all().delete()
    for _, row in df.iterrows(): 
        tc1, _ = TC1.objects.get_or_create(
            code=row["TC I"][0],
            name_cn=row["TC I"].split("|")[1],
            name_en=row["TC I"].split("|")[0][2:],
        )

        tc2, _ = TC2.objects.get_or_create(
            code=row["TC II"][:3],
            name_cn=row["TC II"].split("|")[1],
            name_en=row["TC II"].split("|")[0][4:],
            tc1=tc1,
        )

        tc3, _ = TC3.objects.get_or_create(
            code=row["TC III"][:4],
            name_cn=row["TC III"].split("|")[1],
            name_en=row["TC III"].split("|")[0][5:],
            tc2=tc2,
        )

        tc4, _ = TC4.objects.get_or_create(
            code=row["TC IV"][:5],
            name_cn=row["TC IV"].split("|")[1],
            name_en=row["TC IV"].split("|")[0][6:],
            tc3=tc3,
        )

        subject, _ = Subject.objects.get_or_create(
            name=row["药品名称"],
            tc4=tc4,
            formulation=row["剂型"],
            origin_company=row["生产企业-魔方"] if row["独家/非独家"] == "独家" else None,
        )

        nego, _ = Negotiation.objects.get_or_create(
            subject=subject,
            nego_date = datetime.datetime(year=int(row["医保年份"][:4]),month=1,day=1),
            reimbursement_start = row["协议执行日期"],
            reimbursement_end = row["协议截止日期"],
            nego_type = row["类型"],
            new_indication = D_BOOLEAN[row["适应症变化"]],
            is_exclusive = True if row["独家/非独家"] == "独家" else False,
            price_new = row["价格N0"],
            price_old = row["价格N-1"] if row["价格N-1"] != "-" else None,
            dosage_for_price = row["价格对应规格"],
            note = row["备注"],
        )


if __name__ == "__main__":
    # import_nego()
    # print("Done!", time.process_time())

    from nrdl_price.models import Negotiation
    negos = Negotiation.objects.all()

    for nego in negos:
        if nego.year == 2023 and nego.docs_url is None:
            print(nego)
