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


SOURCE_LIST = ["广东省药品交易中心", "广东省医保局", "福建省医保局"]


def extract_announce(page_url: str, html: str, source: str, page_num: str) -> list:
    slc = etree.HTML(html)
    try:
        src_date = time.strftime("%Y-%m-%d", time.localtime())  # 爬取日期
        domain = urlparse(page_url).netloc  # 域名
        if source == "广东省药品交易中心":
            tree_xp = "//html/body/div[1]/div/div/div[1]/div[2]/div[1]/div/div/a"
            tree = [e for e in slc.xpath(tree_xp)]  # 当页所有公告

            df = pd.DataFrame()
            for e in tree:
                title = e[0][0].text  # 公告标题
                pub_date = time.strftime(
                    "%Y-%m-%d",
                    time.strptime(xp(e, "//div[@class='date']"), "%Y年%m月%d日"),
                )  # 公告日期
                url = e.attrib["href"]  # 公告链接
                df = df.append(
                    {
                        "公告源": source,
                        "爬取日期": src_date,
                        "公告日期": pub_date,
                        "公告标题": title,
                        "域名": domain,
                        "爬取地址": page_url,
                        "公告链接": url,
                    },
                    ignore_index=True,
                )
        elif source == "广东省医保局":
            tree_xp = "/html/body/div[4]/div[2]/ul/li"
            tree = [e for e in slc.xpath(tree_xp)]  # 当页所有公告
            df = pd.DataFrame()
            for e in tree:
                title = e[0].attrib["title"]  # 公告标题
                pub_date = time.strftime(
                    "%Y-%m-%d", time.strptime(e[1].text, "%Y-%m-%d")
                )  # 公告日期
                url = e[0].attrib["href"]  # 公告链接
                df = df.append(
                    {
                        "公告源": source,
                        "爬取日期": src_date,
                        "公告日期": pub_date,
                        "公告标题": title,
                        "域名": domain,
                        "爬取地址": page_url,
                        "公告链接": url,
                    },
                    ignore_index=True,
                )
        elif source == "福建省医保局":
            if page_num == 1:
                tree_xp = (
                    "/html/body/div[1]/div[3]/div/div[2]/div[2]/div[*]/div[*]/ul/li"
                )
            else:
                tree_xp = (
                    "/html/body/div[1]/div[3]/div/div[2]/div[2]/div[2]/div[*]/ul/li"
                )
            tree = [e for e in slc.xpath(tree_xp)]  # 当页所有公告
            df = pd.DataFrame()
            for e in tree:
                title = e[1].attrib["title"]  # 公告标题
                pub_date = time.strftime(
                    "%Y-%m-%d", time.strptime(e[0].text, "%Y-%m-%d")
                )  # 公告日期
                url = e[1].attrib["href"]  # 公告链接
                df = df.append(
                    {
                        "公告源": source,
                        "爬取日期": src_date,
                        "公告日期": pub_date,
                        "公告标题": title,
                        "域名": domain,
                        "爬取地址": page_url,
                        "公告链接": url,
                    },
                    ignore_index=True,
                )

        return df
    except Exception as e:
        cprint(f"内容解析错误: {e}", "white", "on_red")
        pass


def xp(slc, exp: str) -> str:
    """Extract by XPATH"""
    text = slc.xpath(exp)[0].text
    if text and (text != ""):
        text = text.replace("\n", "")
        text = re.sub(r"s+", " ", text)
        return text.strip()
    else:
        return ""


async def get_announce_df(source: str) -> list:
    global BROWSER
    BROWSER = await launch(
        args=PARMS["args"], handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False,
    )
    page = await BROWSER.newPage()
    await page.evaluateOnNewDocument(JS_TEXT)  # 本页刷新后值不变，自动执行js

    page_num = 1
    df_combined = pd.DataFrame()

    if source == "广东省药品交易中心":
        while True:
            try:
                page_url = "https://www.gdmede.com.cn/announcement/?page=%s" % page_num
                await page.goto(page_url)
                xp_for_pageend = "/html/body/div[1]/div/div/div[1]/div[2]/div[1]/div/div[3]/div/ul/li[1]"
                await page.waitForXPath(
                    xp_for_pageend, timeout=5000,
                )  # 等待底部元素加载
                result = await page.content()
                df = extract_announce(page_url, result, source, page_num)
                if df.empty:
                    break
                else:
                    df_combined = pd.concat([df_combined, df], axis=0)
                    print("%s-page%s-%s条公告" % (source, page_num, df_combined.shape[0]))
                    page_num += 1  # 翻页
            except Exception as e:
                cprint(f"翻页循环出现错误: {e}", "white", "on_red")
                break
    elif source == "广东省医保局":
        while True:
            try:
                if page_num == 1:
                    page_url = "http://hsa.gd.gov.cn/zwdt/snkb/index.html"
                else:
                    page_url = "http://hsa.gd.gov.cn/zwdt/snkb/index_%s.html" % page_num
                await page.goto(page_url)
                xp_for_pageend = "/html/body/div[4]/div[2]/div[2]/a[3]"
                await page.waitForXPath(
                    xp_for_pageend, timeout=5000,
                )  # 等待底部元素加载
                result = await page.content()
                df = extract_announce(page_url, result, source, page_num)
                if df.empty:
                    break
                else:
                    df_combined = pd.concat([df_combined, df], axis=0)
                    print("%s-page%s-%s条公告" % (source, page_num, df_combined.shape[0]))
                    page_num += 1  # 翻页
            except Exception as e:
                cprint(f"翻页循环出现错误: {e}", "white", "on_red")
                break
    elif source == "福建省医保局":
        page_url = "https://ybj.fujian.gov.cn/ztzl/yxcg/ggtz/"
        await page.goto(page_url)
        xp_for_pageend = '//a[contains(., "下一页")]'
        await page.waitForXPath(
            xp_for_pageend, timeout=5000,
        )  # 等待底部元素加载
        result = await page.content()
        df_combined = extract_announce(page_url, result, source, page_num)
        print("%s-page%s-%s条公告" % (source, 1, df_combined.shape[0]))
        while True:
            try:
                btn_nextpage = await page.xpath('//a[contains(., "下一页")]')
                await btn_nextpage[0].click()
                page_num += 1  # 翻页
                await asyncio.sleep(1)
                result = await page.content()
                df = extract_announce(page_url, result, source, page_num)
                if df.empty:
                    break
                else:
                    df_combined = pd.concat([df_combined, df], axis=0)
                    print("%s-page%s-%s条公告" % (source, page_num, df_combined.shape[0]))

            except Exception as e:
                cprint(f"翻页循环出现错误: {e}", "white", "on_red")
                break

    await BROWSER.close()

    return df_combined


def import_django(df):
    l = []
    for item in df.values:
        if item[4] in item[3]:
            url = item[3]
        else:
            if item[3][:4] == "http":
                url = item[3]
            elif item[3][:2] == "./":
                url = item[5] + item[3][2:]
            else:
                url = item[5].split("://")[0] + "://" + item[4] + item[3]
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
        for source in SOURCE_LIST:
            df = asyncio.get_event_loop().run_until_complete(get_announce_df(source))
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

    # df = pd.read_excel("./test.xlsx")
    # import_django(df)
