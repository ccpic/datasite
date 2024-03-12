#!/usr/bin/env python
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datasite.settings")

import django

django.setup()

import time
from sqlalchemy import create_engine
import pandas as pd

import numpy as np
from kol.models import Kol, Record
from django.contrib.auth.models import User

if __name__ == "__main__":
    d = {
        "福建": "杭州MSL",
        "江西": "杭州MSL",
        "浙江": "杭州MSL",
        "江苏": "南京MSL",
        "山东": "南京MSL",
        "上海": "上海MSL",
        "安徽": "上海MSL",
        "四川": "成都MSL",
        "重庆": "成都MSL",
        "陕西": "成都MSL",
        "甘肃": "成都MSL",
        "新疆": "成都MSL",
        "广东": "广州MSL",
        "广西": "广州MSL",
        "海南": "广州MSL",
        "北京": "北京MSL",
        "天津": "北京MSL",
        "河北": "北京MSL",
        "黑龙江": "北京MSL",
        "吉林": "北京MSL",
        "辽宁": "北京MSL",
        "湖北":  "武汉MSL",
        "湖南":  "武汉MSL",
        "河南":  "武汉MSL",
    }

    for key, value in d.items():
        user = User.objects.get(username=value)
        kols = Kol.objects.filter(hospital__province=key)
        records = Record.objects.filter(kol__hospital__province=key)
        kols.update(pub_user=user)
        records.update(pub_user=user)
