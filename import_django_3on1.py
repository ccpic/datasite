#!/usr/bin/env python
import os
import time
from sqlalchemy import create_engine
import pandas as pd
import django
import numpy as np

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datasite.settings")
django.setup()

from internal_sales.views import D_MODEL  # noqa: E402

engine = create_engine("mssql+pymssql://(local)/Internal_sales")
table = "sales"

D_BOOLEAN = {"是": True, "否": False}


def importModel(dict):
    for key in dict:
        sql = "SELECT Distinct " + key + " FROM " + table
        df = pd.read_sql(sql=sql, con=engine)
        df.dropna(inplace=True)
        print(df)
        li = []
        for item in df.values:
            li.append(dict[key](name=item[0]))

        dict[key].objects.all().delete()
        dict[key].objects.bulk_create(li)


# 为KOL系统导入医院对象
def import_hp():
    from kol.models import Hospital

    sql = "SELECT Distinct HP_ID, HP_NAME, PROVINCE, CITY, LEVEL, DSM_NAME From sales where PRODUCT = '信立坦'"
    df = pd.read_sql(sql=sql, con=engine)
    df.dropna(inplace=True)
    df.drop_duplicates(subset=["HP_ID"], inplace=True)
    df.drop_duplicates(subset=["HP_NAME"], inplace=True)
    df.to_excel("test.xlsx")
    print(df)
    li = []
    for item in df.values:
        li.append(
            Hospital(
                xltid=item[0],
                name=item[1],
                province=item[2],
                city=item[3],
                decile=item[4],
                dsm=item[5],
            )
        )

    Hospital.objects.all().delete()
    Hospital.objects.bulk_create(li)


def update_hp():
    from kol.models import Hospital

    hps = Hospital.objects.all()
    df = pd.read_excel("test.xlsx", engine="openpyxl")
    df = df.replace({np.nan: None})
    print(df)
    for hp in hps:
        print(hp.name, hp.decile, df[df["xltid"] == hp.xltid]["decile_enar"].values[0])
        hp.decile = df[df["xltid"] == hp.xltid]["decile_enar"].values[0]
        hp.save()


if __name__ == "__main__":
    # update_hp()
    importModel(D_MODEL)
    print("Done!", time.process_time())
