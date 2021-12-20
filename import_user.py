#!/usr/bin/env python
import sys
import os

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datasite.settings")
import django

django.setup()
import time
from sqlalchemy import create_engine
import pandas as pd
import django
import datetime
import math
import numpy as np
from django.contrib.auth.models import User, Group
from xpinyin import Pinyin


if __name__ == "__main__":
    p = Pinyin()
    df = pd.read_excel("user.xlsx")
    group = Group.objects.get(name="医学信息贡献者")
    for index, value in df.iterrows():
        username = value[0]
        password = "".join(p.get_pinyin(value[0]).split("-"))
        print(username, password)

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User(username=username)

        user.set_password(password)
        user.is_staff = True
        user.save()
        
        if user.groups.filter(name="医学信息贡献者").exists() is False:
            group.user_set.add(user)
            group.save()
