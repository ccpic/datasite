from django.shortcuts import render
import requests
import time, datetime

# while True:
#     now = datetime.datetime.now()
#     if now.second == 15:
#         print(now)
#         time.sleep(10) #sleep almost 24h
#     else:
#         time.sleep(1) # 每个一段时间检查时间

url = "https://ranking.m.jd.com/comLandingPage/comLandingPage?contentId=171523&rankType=10&fromName=main_channel&sku=&preSrc=undefined&hideAd=xxx&ptag="
r = requests.get(url)
r.encoding = "utf-8"
print(r.text)
