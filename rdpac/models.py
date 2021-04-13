from django.db import models
import datetime
from django.db.models import Avg, Count, Min, Sum

CURRENT_YEAR = 2020
YEAR_CHOICES = [(r, r) for r in range(2013, CURRENT_YEAR + 1)]


class Company(models.Model):
    name_en = models.CharField(max_length=20, verbose_name="英文名", unique=True)
    name_cn = models.CharField(max_length=20, verbose_name="中文名", unique=True)
    abbr = models.CharField(max_length=4, verbose_name="名称缩写", unique=True)
    country_code = models.CharField(
        max_length=30, verbose_name="国家代码"
    )  # 填写2位小写英文国家代码以便后续前端匹配旗帜， 如us, uk
    logo = models.ImageField(upload_to='logos/', verbose_name="公司Logo")
    
    
    class Meta:
        verbose_name = "MNC"
        ordering = ["name_en"]

    def __str__(self):
        return "%s %s" % (self.name_en, self.name_cn)

    @property
    def annual_netsales(self, years=[CURRENT_YEAR]):
        qs = self.sales.filter(year__in=years)
        if qs.exists():
            netsales = qs.aggregate(Sum("netsales_value"))["netsales_value__sum"]
            return netsales

    @property
    def latest_netsales_gr(self):
        qs = self.sales.filter(year=CURRENT_YEAR)
        if qs.exists():
            netsales = qs.aggregate(Sum("netsales_value"))["netsales_value__sum"]
        else:
            netsales = 0

        qs = self.sales.filter(year=CURRENT_YEAR - 1)
        if qs.exists():
            netsales_ya = qs.aggregate(Sum("netsales_value"))["netsales_value__sum"]
        else:
            netsales_ya = 0

        try:
            return netsales / netsales_ya - 1
        except ZeroDivisionError:
            return None


class Drug(models.Model):
    molecule_en = models.CharField(max_length=30, verbose_name="英文通用名")
    molecule_cn = models.CharField(max_length=30, verbose_name="中文通用名")
    product_name_en = models.CharField(
        max_length=30, verbose_name="英文产品名", unique=True, blank=True
    )
    product_name_cn = models.CharField(
        max_length=30, verbose_name="中文产品名", unique=True, blank=True
    )

    class Meta:
        verbose_name = "药物"
        ordering = ["molecule_en"]

    def __str__(self):
        return "%s %s" % (self.molecule_en, self.molecule_cn)

    @property
    def annual_netsales(self, years=[CURRENT_YEAR]):
        qs = self.sales.filter(year__in=years)
        if qs.exists():
            netsales = qs.aggregate(Sum("netsales_value"))["netsales_value__sum"]
            return netsales

    @property
    def latest_netsales_gr(self):
        qs = self.sales.filter(year=CURRENT_YEAR)
        if qs.exists():
            netsales = qs.aggregate(Sum("netsales_value"))["netsales_value__sum"]
        else:
            netsales = 0

        qs = self.sales.filter(year=CURRENT_YEAR - 1)
        if qs.exists():
            netsales_ya = qs.aggregate(Sum("netsales_value"))["netsales_value__sum"]
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
        return self.netsales_value / netsales_company

    def __str__(self):
        return "%s %s %s %s" % (self.company, self.drug, self.year, self.netsales_value)

