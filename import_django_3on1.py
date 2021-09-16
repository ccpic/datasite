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

from internal_sales.views import *


engine = create_engine("mssql+pymssql://(local)/Internal_sales")
table = "sales"

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


if __name__ == "__main__":
    importModel(D_MODEL)
    print("Done!", time.process_time())
