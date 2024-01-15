from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote import webelement
from selenium.webdriver import ChromeOptions
import requests
import time
import os
import io

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal


class NHSA_Crawler(object):
    def __init__(self):
        options = ChromeOptions()
        options.add_argument("--headless")  # 无头模式，不打开浏览器图形界面
        prefs = {
            "profile.default_content_setting_values": {"notifications": 2},
            "credentials_enable_service": False,
            "profile": {"password_manager_enabled": False},
        }
        options.add_experimental_option("prefs", prefs)
        options.add_argument("--no-sandbox")  # 禁止沙盒模式
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36"
        )
        # options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")  # 禁用扩展
        options.add_argument("--disable-gpu")  # 禁用GPU加速
        # option.add_argument('--proxy-server=http://127.0.0.1:8080') # 需要时可挂代理
        # options.add_experimental_option("excludeSwitches", ["enable-automation"])
        # options.add_experimental_option("detach", True)
        # options.add_argument("--ignore-certificate-errors")
        # options.add_argument("--ignore-ssl-errors")
        options.page_load_strategy = "eager"  # 更快的加载策略

        self.driver = webdriver.Chrome(options=options)

        # 反检测
        # 移除webdriver
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
            },
        )

        self.driver.set_page_load_timeout(30)
        self.timeout = WebDriverWait(self.driver, 30)
        self.wait = WebDriverWait(self.driver, 10)  # 等待时间
        self.login_success = False

    def wait_and_get(self, by: Literal["id", "xpath"], desc: str) -> webelement:
        """等待网页元素出现并获取

        Args:
            by (Literal["id", "xpath"]): 根据什么定位，id还是xpath
            desc (str): 具体定位内容

        Return:
            webelement: 网页元素
        """

        by = by.upper()
        if by == "XPATH":
            return self.wait.until(EC.presence_of_element_located((By.XPATH, desc)))
        if by == "ID":
            return self.wait.until(EC.presence_of_element_located((By.ID, desc)))

    def get_pdf(
        self,
        url: str,
        row_start: int,
        row_end: int,
        if_in: Literal["目录内", "目录外"],
        year: Literal["2022", "2023"],
    ) -> None:
        """获取该页面所有产品的名称和pdf

        Args:
            url (str): 医保局网页网址
            row_start (int): 开始行数
            row_end (int): 结束行数
            if_in (Literal["目录内", "目录外"]): 是否已在目录内，主要用来创建文件夹名
            year (Literal["2022", "2023"]): 医保年份，主要用于创建文件夹名
        """

        browser = self.driver
        browser.maximize_window()  # 最大化窗口

        browser.get(url)
        time.sleep(3)

        for i in range(row_start, row_end):
            print(i)
            if year == "2022":
                xpath = f"/html/body/div[2]/div/div[4]/div/div/div[2]/div[4]/p[{i}]"
            elif year == "2023":
                xpath = f"/html/body/div[2]/div[4]/div/div/div[2]/div[4]/p[{i}]"

            p = self.wait_and_get(
                "XPATH", xpath
            ).text  # p的值格式为YPSW202300010-戊酸二氟可龙乳膏：药品信息.pdf、信息摘要.ppt
            product_name = p.split("：")[0].strip().split("-")[1].strip()  # 从p中提取产品名称
            product_name = product_name.replace("/", "")  # 产品名称中有斜杠的要移除，否则会导致文件夹路径错误
            save_folder = f"NRDL_pdf/{year}/{if_in}/{product_name}"

            # 检查并创建文件夹
            if not os.path.exists(save_folder):
                os.makedirs(save_folder)

            # 获取申报材料的pdf链接
            pdf_link1 = self.wait_and_get("XPATH", xpath + "/a[1]").get_attribute(
                "href"
            )

            if pdf_link1:
                save_path = os.path.join(save_folder, f"{product_name}_申报材料.pdf")
                self.download_pdf(save_path, pdf_link1)

            # 获取信息摘要的pdf链接，并不是每个产品都有
            try:
                pdf_link2 = self.wait_and_get("XPATH", xpath + "/a[2]").get_attribute(
                    "href"
                )
            except:
                pdf_link2 = None
                pass

            if pdf_link2:
                save_path = os.path.join(save_folder, f"{product_name}_信息摘要.pptx")
                self.download_pdf(save_path, pdf_link2)

    def download_pdf(self, save_path: str, pdf_url: str) -> None:
        """下载pdf文件

        Args:
            save_path (str): pdf文件的本地保存路径（含文件名）
            pdf_url (str): pdf下载地址
        """

        send_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
            "Connection": "keep-alive",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.8",
        }
        response = requests.get(pdf_url, headers=send_headers)
        bytes_io = io.BytesIO(response.content)
        with open(save_path, mode="wb") as f:
            f.write(bytes_io.getvalue())
            print(f"{save_path}下载成功！")


if __name__ == "__main__":
    url_2022 = "http://www.nhsa.gov.cn/art/2022/9/6/art_152_8853.html"
    url_2023 = "http://www.nhsa.gov.cn/art/2023/8/18/art_152_11182.html"
    c = NHSA_Crawler()
    # c.get_pdf(url_2022, 2, 233, "目录外", "2022")
    # c.get_pdf(url_2022, 234, 389, "目录内", "2022")
    c.get_pdf(url_2023, 55, 269, "目录外", "2023")  # 目录外品种
    c.get_pdf(url_2023, 270, 440, "目录内", "2023")  # 目录内品种
