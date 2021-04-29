from django.db import models
import datetime
from django.db.models import Avg, Count, Min, Sum, F
import pandas as pd
from django_pivot.pivot import pivot

CURRENT_YEAR = 2020
YEARS = [r for r in range(2013, CURRENT_YEAR + 1)]
YEAR_CHOICES = [(r, r) for r in range(2013, CURRENT_YEAR + 1)]


def get_sales_by_year(lst, target_year):
    for item in lst:
        if item["year"] == target_year:
            return item["netsales_value__sum"]


class Company(models.Model):
    name_en = models.CharField(max_length=30, verbose_name="英文名", unique=True)
    name_cn = models.CharField(max_length=10, verbose_name="中文名", unique=True)
    abbr = models.CharField(max_length=4, verbose_name="名称缩写", unique=True)
    country_code = models.CharField(
        max_length=30, verbose_name="国家代码"
    )  # 填写2位小写英文国家代码以便后续前端匹配旗帜， 如us, uk
    logo = models.ImageField(
        upload_to="logos/", default="logos/default.png", verbose_name="公司Logo"
    )

    class Meta:
        verbose_name = "MNC"
        ordering = ["name_en"]

    def __str__(self):
        return "%s %s" % (self.name_en, self.name_cn)

    @property
    def performance_matrix(self):
        qs = self.sales.all()
        if qs.exists():
            result = list(
                qs.values("year").order_by("year").annotate(Sum(F("netsales_value")))
            )
        qs_all = Sales.objects.all()
        result_all = list(
            qs_all.values("year").order_by("year").annotate(Sum(F("netsales_value")))
        )
        if qs.exists():
            for item in result:
                try:
                    item["annual_uplift"] = item[
                        "netsales_value__sum"
                    ] - get_sales_by_year(result, item["year"] - 1)
                except:
                    item["annual_uplift"] = None

                try:
                    item["annual_gr"] = (
                        item["netsales_value__sum"]
                        / get_sales_by_year(result, item["year"] - 1)
                        - 1
                    )
                except:
                    item["annual_gr"] = None

                try:
                    item["company_share"] = item[
                        "netsales_value__sum"
                    ] / get_sales_by_year(result_all, item["year"])
                except:
                    item["company_share"] = None

            return result

    @property
    def drugs(self):
        qs = self.sales.all().order_by("drug_id")
        data = list(
            pivot(queryset=qs, rows="drug_id", column="year", data="netsales_value").order_by("-2020")
        )

        for drug_sale in data:
            drug_sale["molecule_en"] = Drug.objects.get(
                pk=drug_sale["drug_id"]
            ).molecule_en
            drug_sale["molecule_cn"] = Drug.objects.get(
                pk=drug_sale["drug_id"]
            ).molecule_cn
            drug_sale["product_name_en"] = Drug.objects.get(
                pk=drug_sale["drug_id"]
            ).product_name_en
            drug_sale["product_name_cn"] = Drug.objects.get(
                pk=drug_sale["drug_id"]
            ).product_name_cn

        return data

    @property
    def sales_by_year(self):
        qs = self.sales.all()
        if qs.exists():
            return qs.values("year").order_by("year").annotate(Sum(F("netsales_value")))

    @property
    def latest_annual_netsales(self):
        if self.sales_by_year is not None:
            qs = self.sales_by_year.filter(year=CURRENT_YEAR)
            if len(qs) == 1:
                return qs.first()["netsales_value__sum"]
            else:
                return 0

    @property
    def latest_annual_netsales_gr(self):
        if self.sales_by_year is not None:
            netsales = self.latest_annual_netsales
            qs_ya = self.sales_by_year.filter(year=CURRENT_YEAR - 1)
            if len(qs_ya) == 1:
                netsales_ya = qs_ya.first()["netsales_value__sum"]
            else:
                netsales_ya = 0

            try:
                return netsales / netsales_ya - 1
            except ZeroDivisionError:
                return None


class Drug(models.Model):
    molecule_en = models.CharField(max_length=100, verbose_name="英文通用名")
    molecule_cn = models.CharField(max_length=50, verbose_name="中文通用名")
    product_name_en = models.CharField(
        max_length=30, verbose_name="英文产品名", unique=True, blank=True
    )
    product_name_cn = models.CharField(max_length=30, verbose_name="中文产品名", blank=True)

    class Meta:
        verbose_name = "药物"
        ordering = ["molecule_en"]

    def __str__(self):
        return "%s %s (%s %s)" % (
            self.product_name_en,
            self.product_name_cn,
            self.molecule_en,
            self.molecule_cn,
        )

    @property
    def company(self):
        qs = self.sales.all()
        if qs.exists():
            return qs.last().company
    
    @property
    def performance_matrix(self):
        qs = self.sales.all()
        if qs.exists():
            result = list(
                qs.values("year").order_by("year").annotate(Sum(F("netsales_value")))
            )
        qs_all = Sales.objects.all()
        result_all = list(
            qs_all.values("year").order_by("year").annotate(Sum(F("netsales_value")))
        )

        for item in result:
            try:
                item["annual_uplift"] = item["netsales_value__sum"] - get_sales_by_year(
                    result, item["year"] - 1
                )
            except:
                item["annual_uplift"] = None

            try:
                item["annual_gr"] = (
                    item["netsales_value__sum"]
                    / get_sales_by_year(result, item["year"] - 1)
                    - 1
                )
            except:
                item["annual_gr"] = None

            try:
                item["company_share"] = item["netsales_value__sum"] / get_sales_by_year(
                    result_all, item["year"]
                )
            except:
                item["company_share"] = None

        return result

    @property
    def sales_by_year(self):
        qs = self.sales.all()
        if qs.exists():
            return qs.values("year").order_by("year").annotate(Sum(F("netsales_value")))

    @property
    def latest_annual_netsales(self):
        qs = self.sales_by_year.filter(year=CURRENT_YEAR)
        if len(qs) == 1:
            return qs.first()["netsales_value__sum"]
        else:
            return 0

    @property
    def latest_annual_netsales_gr(self):
        netsales = self.latest_annual_netsales
        qs_ya = self.sales_by_year.filter(year=CURRENT_YEAR - 1)
        if len(qs_ya) == 1:
            netsales_ya = qs_ya.first()["netsales_value__sum"]
        else:
            netsales_ya = 0

        try:
            return netsales / netsales_ya - 1
        except ZeroDivisionError:
            return None


class Sales(models.Model):

    drug = models.ForeignKey(
        Drug, on_delete=models.CASCADE, verbose_name="药物", related_name="sales"
    )
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, verbose_name="MNC", related_name="sales"
    )
    year = models.IntegerField(verbose_name="年份", choices=YEAR_CHOICES)
    netsales_value = models.FloatField(verbose_name="发货纯销(RMB)")

    class Meta:
        verbose_name = "销售数据"
        verbose_name_plural = "销售数据"
        ordering = ["company", "drug", "year"]
        unique_together = ["company", "drug", "year"]

    @property
    def get_year(self):
        date = datetime.strptime("%Y", self.year)
        return date

    @property
    def annual_gr(self):  # 年增长率
        try:
            return (
                self.netsales_value
                / self.drug.sales.get(drug=self.drug, year=self.year - 1).netsales_value
                - 1
            )
        except:
            return None

    @property
    def annual_uplift(self):  # 年净增长
        try:
            return (
                self.netsales_value
                - self.drug.sales.get(drug=self.drug, year=self.year - 1).netsales_value
            )
        except:
            return None

    @property
    def annual_contrib(self):  # 年贡献率（占公司）
        qs = self.company.sales.filter(year=self.year)
        if qs.exists():
            netsales_company = qs.aggregate(Sum("netsales_value"))[
                "netsales_value__sum"
            ]
        try:
            return self.netsales_value / netsales_company
        except:
            return None

    def __str__(self):
        return "%s %s %s %s" % (self.company, self.drug, self.year, self.netsales_value)

