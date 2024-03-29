from django.db import models
import numpy as np
from typing import Optional
import os
from django.conf import settings



class TC1(models.Model):
    code = models.CharField(verbose_name="编码", max_length=1)
    name_cn = models.CharField(verbose_name="中文名称", max_length=50)
    name_en = models.CharField(verbose_name="英文名称", max_length=50)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name_en}|{self.name_cn}"


class TC2(models.Model):
    code = models.CharField(verbose_name="编码", max_length=3)
    name_cn = models.CharField(verbose_name="中文名称", max_length=50)
    name_en = models.CharField(verbose_name="英文名称", max_length=50)
    tc1 = models.ForeignKey(
        TC1,
        verbose_name="TC I",
        on_delete=models.CASCADE,
        related_name="tc1_tc2s",
    )

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name_en}|{self.name_cn}"


class TC3(models.Model):
    code = models.CharField(verbose_name="编码", max_length=4)
    name_cn = models.CharField(verbose_name="中文名称", max_length=50)
    name_en = models.CharField(verbose_name="英文名称", max_length=50)
    tc2 = models.ForeignKey(
        TC2,
        verbose_name="TC II",
        on_delete=models.CASCADE,
        related_name="tc2_tc3s",
    )

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name_en}|{self.name_cn}"


class TC4(models.Model):
    code = models.CharField(verbose_name="编码", max_length=5)
    name_cn = models.CharField(verbose_name="中文名称", max_length=50)
    name_en = models.CharField(verbose_name="英文名称", max_length=50)
    tc3 = models.ForeignKey(
        TC3,
        verbose_name="TC III",
        on_delete=models.CASCADE,
        related_name="tc3_tc4s",
    )

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name_en}|{self.name_cn}"


class Subject(models.Model):
    name = models.CharField(verbose_name="名称", max_length=50)
    tc4 = models.ForeignKey(
        TC4,
        verbose_name="TC IV",
        on_delete=models.CASCADE,
        related_name="tc4_subjects",
    )
    formulation = models.CharField(verbose_name="剂型", max_length=20)
    origin_company = models.CharField(
        verbose_name="原研公司", max_length=50, null=True, blank=True
    )

    class Meta:
        verbose_name = "谈判主体"
        verbose_name_plural = "谈判主体"
        ordering = ["tc4__code", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.tc4})"


class Negotiation(models.Model):
    TYPE_CHOICES = [
        ("新增分子", "新增分子"),
        ("新增剂型", "新增剂型"),
        ("非谈判转谈判", "非谈判转谈判"),
        ("续约", "续约"),
    ]
    subject = models.ForeignKey(
        Subject,
        verbose_name="谈判品种",
        on_delete=models.CASCADE,
        related_name="subject_negotiations",
    )
    nego_date = models.DateField(verbose_name="谈判日期")
    reimbursement_start = models.DateField(verbose_name="协议执行日期")
    reimbursement_end = models.DateField(verbose_name="协议截止日期")
    nego_type = models.CharField(
        choices=TYPE_CHOICES, verbose_name="谈判类型", max_length=10
    )
    new_indication = models.BooleanField(verbose_name="是否更改适应症")
    is_exclusive = models.BooleanField(verbose_name="是否独家品种")
    price_new = models.FloatField(verbose_name="谈判后价格")
    price_old = models.FloatField(
        verbose_name="谈判前价格",
        blank=True,
        null=True,
    )
    dosage_for_price = models.CharField(verbose_name="价格对应规格", max_length=200)
    note = models.TextField(verbose_name="备注", blank=True, null=True)

    class Meta:
        verbose_name = "医保谈判"
        verbose_name_plural = "医保谈判"
        ordering = ["subject__name", "nego_date"]

    def __str__(self) -> str:
        return f"{self.subject} ({self.year})"

    @property
    def year(self) -> int:
        return int(self.nego_date.year)

    @property
    def price_change(self) -> Optional[float]:
        try:
            change = self.price_new / self.price_old - 1
        except Exception:
            change = np.nan
        return change

    @property
    def docs_url(self) -> str:
        base_url = "/NRDL_pdf/"
        year = str(self.year)
        sub_dir = f"{base_url}{year}/{self.subject.name}/"
        dir = f"{settings.STATICFILES_DIRS[0]}{sub_dir}"

        try:
            docs = [f"{dir}{f}" for f in os.listdir(dir)]
        except FileNotFoundError:
            docs = None
        return docs


