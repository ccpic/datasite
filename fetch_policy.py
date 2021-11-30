from django.shortcuts import render
import asyncio
import pandas as pd
from pyppeteer import browser, launch, target
import time
import re
from lxml import etree
from termcolor import cprint
from urllib.parse import urlparse
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datasite.settings")
django.setup()

from policy_feed.models import Announce


PARMS = {
    "headless": False,
    "args": [
        "--disable-infobars",  # 关闭自动化提示框
        "--log-level=30",  # 日志保存等级， 建议设置越好越好，要不然生成的日志占用的空间会很大 30为warning级别
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36",  # UA
        # '--single-process',
        # '--disable-gpu',
        "--no-sandbox",  # 关闭沙盒模式
        "--start-maximized",  # 窗口最大化模式
        # '--proxy-server=127.0.0.1:1080'
        "--window-size=1680,1050",  # 窗口大小
        # '--proxy-server=http://localhost:1080'  # 代理
        # '--enable-automation'
    ],
}

JS_TEXT = """
    () =>{
        Object.defineProperties(navigator, { webdriver:{ get: () => false } });
        window.navigator.chrome = { runtime: {},  };
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins',   { get: () => [1, 2, 3, 4, 5,6], });
    }
    """


D_SOURCE = {
    "广东省药品交易中心": {
        "page1_url": "https://www.gdmede.com.cn/announcement/?page=1",
        "page_url": "https://www.gdmede.com.cn/announcement/?page=%s",
        "page_num_adjust": 0,
        "xp_pageend": "/html/body/div[1]/div/div/div[1]/div[2]/div[1]/div/div[3]/div/ul/li[1]",
        "xp_pub_date": '//div[@class="date"]/text()',
        "xp_title": '//div[@class="title"]/span/text()',
        "xp_url": '//a[@class="item-wrap"]/@href',
        "date_format": "%Y年%m月%d日",
    },
    "广东省医保局": {
        "page1_url": "http://hsa.gd.gov.cn/zwdt/snkb/index.html",
        "page_url": "http://hsa.gd.gov.cn/zwdt/snkb/index_%s.html",
        "page_num_adjust": 0,
        "xp_pageend": "/html/body/div[4]/div[2]/div[2]/a[3]",
        "xp_pub_date": "//html/body/div[4]/div[2]/ul/li/i/text()",
        "xp_title": "//html/body/div[4]/div[2]/ul/li/a/@title",
        "xp_url": "//html/body/div[4]/div[2]/ul/li/a/@href",
        "date_format": "",
    },
    "北京市医保局_药品公告": {
        "page1_url": "http://ybj.beijing.gov.cn/zczxs/2020_ycgga/index.html",
        "page_url": "http://ybj.beijing.gov.cn/zczxs/2020_ycgga/index_%s.html",
        "page_num_adjust": -1,
        "xp_pageend": "",
        "xp_pub_date": "//html/body/div[4]/div/div[2]/ul/li/text()",
        "xp_title": "/html/body/div[4]/div/div[2]/ul/li/a/text()",
        "xp_url": "/html/body/div[4]/div/div[2]/ul/li/a/@href",
        "date_format": "",
    },
    "福建省医保局": {
        "page1_url": "https://ybj.fujian.gov.cn/ztzl/yxcg/ggtz/",
        "page_url": "",
        "page_num_adjust": None,
        "xp_pageend": '//a[contains(., "下一页")]',
        "xp_pub_date": "",
        "xp_title": "",
        "xp_url": "",
        "date_format": "",
    },
}


def extract_announce(
    page_url: str, html: str, source: str, xp: dict, page_num: str
) -> list:
    slc = etree.HTML(html)  # 解析树

    if source == "福建省医保局":  # 福建医保局网页的特殊情况
        if page_num == 1:
            xp_pub_date = "/html/body/div[1]/div[3]/div/div[2]/div[2]/div[*]/div[*]/ul/li/span/text()"
            xp_title = "/html/body/div[1]/div[3]/div/div[2]/div[2]/div[*]/div[*]/ul/li/a/@title"
            xp_url = (
                "/html/body/div[1]/div[3]/div/div[2]/div[2]/div[*]/div[*]/ul/li/a/@href"
            )
        else:
            xp_pub_date = "/html/body/div[1]/div[3]/div/div[2]/div[2]/div[2]/div[*]/ul/li/span/text()"
            xp_title = "/html/body/div[1]/div[3]/div/div[2]/div[2]/div[2]/div[*]/ul/li/a/@title"
            xp_url = (
                "/html/body/div[1]/div[3]/div/div[2]/div[2]/div[2]/div[*]/ul/li/a/@href"
            )
    else:  # 一般情况
        xp_pub_date = xp["xp_pub_date"]
        xp_title = xp["xp_title"]
        xp_url = xp["xp_url"]

    date_format = xp["date_format"]

    try:
        src_date = time.strftime("%Y-%m-%d", time.localtime())  # 爬取日期
        domain = urlparse(page_url).netloc  # 域名

        list_pub_date = strip_list(slc.xpath(xp_pub_date), date_format=date_format,)
        list_title = strip_list(slc.xpath(xp_title))
        list_url = strip_list(slc.xpath(xp_url))

        df = pd.DataFrame(
            list(zip(list_pub_date, list_title, list_url)),
            columns=["公告日期", "公告标题", "公告链接"],
        )

        df["公告源"] = source
        df["爬取日期"] = src_date
        df["域名"] = domain
        df["爬取地址"] = page_url

        return df
    except Exception as e:
        cprint(f"内容解析错误: {e}", "white", "on_red")
        pass


def strip_list(list_text: list, date_format: str = "") -> list:
    list_new = []
    for text in list_text:
        text = strip(text)
        if date_format != "":
            text = time.strftime(
                "%Y-%m-%d", time.strptime(text, date_format),
            )  # 根据格式日期文本标准化
        list_new.append(text)
    return list_new


def strip(text: str) -> str:
    if text and (text != ""):
        text = text.replace("\n", "")
        text = re.sub(r"\s+", " ", text)
        return text.strip()
    else:
        return ""


async def get_announce_df(source: str, param: dict) -> list:
    global BROWSER
    BROWSER = await launch(
        args=PARMS["args"], handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False,
    )
    page = await BROWSER.newPage()
    await page.evaluateOnNewDocument(JS_TEXT)  # 本页刷新后值不变，自动执行js

    page_num = 1
    df_combined = pd.DataFrame()

    if param["page_url"] == "":  # 翻页没哟体现在url上的解决方法，模拟点击下一页按钮后抓取内容
        page_url = param["page1_url"]
        await page.goto(page_url)
        xp_for_pageend = param["xp_pageend"]
        await page.waitForXPath(
            xp_for_pageend, timeout=5000,
        )  # 等待底部元素加载，本场景下底部元素设置为翻页按钮，之后同时用于点击翻页
        result = await page.content()
        df_combined = extract_announce(page_url, result, source, param, page_num)
        print("%s-page%s-%s条公告" % (source, 1, df_combined.shape[0]))
        while True:
            try:
                btn_nextpage = await page.xpath(param["xp_pageend"])  # 翻页按钮
                await btn_nextpage[0].click()
                page_num += 1  # 翻页
                await asyncio.sleep(1)
                result = await page.content()
                df = extract_announce(page_url, result, source, param, page_num)
                if df.empty:
                    break
                else:
                    df_combined = pd.concat([df_combined, df], axis=0)
                    print("%s-page%s-%s条公告" % (source, page_num, df_combined.shape[0]))

            except Exception as e:
                cprint(f"翻页循环出现错误: {e}", "white", "on_red")
                break
    else:  # 翻页体现在url上的解决方法，根据页码循环即可
        while True:
            try:
                if page_num == 1:
                    page_url = param["page1_url"]
                else:
                    page_url = param["page_url"] % (page_num + param["page_num_adjust"])
                await page.goto(page_url)  # 跳转页面
                if param["xp_pageend"] == "":
                    await asyncio.sleep(1)
                else:
                    await page.waitForXPath(
                        param["xp_pageend"], timeout=5000,
                    )  # 等待底部元素加载
                result = await page.content()  # 爬取内容
                df = extract_announce(
                    page_url, result, source, param, page_num
                )  # 调用解析函数
                if df.empty:
                    break
                else:
                    df_combined = pd.concat([df_combined, df], axis=0)
                    print("%s-page%s-%s条公告" % (source, page_num, df_combined.shape[0]))
                    page_num += 1  # 翻页
            except Exception as e:
                cprint(f"翻页循环出现错误: {e}", "white", "on_red")
                break
    await BROWSER.close()

    return df_combined


def import_django(df):
    df = df.reindex(columns=["公告日期", "公告标题", "公告源", "公告链接", "域名", "爬取地址", "爬取日期"])

    l = []
    for item in df.values:
        prefix = item[5].split("://")[0]
        domain = item[4]
        target_url = item[3]
        if item[5][-1] == "/":
            page_url = item[5]
        else:
            page_url = item[5].rsplit("/", 1)[0] + "/"

        if domain in target_url:
            url = target_url
        else:
            if target_url[:4] == "http":
                url = target_url
            elif target_url[:2] == "./":
                url = page_url + target_url[2:]
            else:
                url = prefix + "://" + domain + target_url
        l.append(
            Announce(
                pub_date=item[0],
                title=item[1],
                source=item[2],
                url=url,
                fetch_date=item[6],
            )
        )

    Announce.objects.all().delete()
    Announce.objects.bulk_create(l)


if __name__ == "__main__":
    try:
        time_start = time.time()
        cprint("Start running...", "white", "on_green")

        df_combined = pd.DataFrame()
        for key, value in D_SOURCE.items():
            df = asyncio.get_event_loop().run_until_complete(
                get_announce_df(source=key, param=value)
            )
            df_combined = pd.concat([df_combined, df])
        print(df_combined)
        import_django(df_combined)
        df_combined.to_excel(
            "test%s.xlsx" % time.strftime("%Y%m%d%H%M%S", time.localtime()), index=False
        )
        cprint("Data saved", "white", "on_green")

        time_end = time.time()
        cprint(f"Total time: {str(time_end-time_start)[:5]}s.", "white", "on_green")
    except KeyboardInterrupt as k:
        cprint("\nKey pressed to interrupt...", "white", "on_red")
