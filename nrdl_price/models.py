from django.db import models
import numpy as np
from typing import Union, Optional


class TC1(models.Model):
    code = models.CharField(verbose_name="编码", max_length=1)
    name_cn = models.CharField(verbose_name="中文名称", max_length=30)
    name_en = models.CharField(verbose_name="英文名称", max_length=30)

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name_cn}|{self.name_en}"


class TC2(models.Model):
    code = models.CharField(verbose_name="编码", max_length=3)
    name_cn = models.CharField(verbose_name="中文名称", max_length=30)
    name_en = models.CharField(verbose_name="英文名称", max_length=30)
    tc1 = models.ForeignKey(
        TC1,
        verbose_name="TC I",
        on_delete=models.CASCADE,
        related_name="tc1_tc2s",
    )

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name_cn}|{self.name_en}"


class TC3(models.Model):
    code = models.CharField(verbose_name="编码", max_length=4)
    name_cn = models.CharField(verbose_name="中文名称", max_length=30)
    name_en = models.CharField(verbose_name="英文名称", max_length=30)
    tc2 = models.ForeignKey(
        TC2,
        verbose_name="TC II",
        on_delete=models.CASCADE,
        related_name="tc2_tc3s",
    )

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name_cn}|{self.name_en}"


class TC4(models.Model):
    code = models.CharField(verbose_name="编码", max_length=5)
    name_cn = models.CharField(verbose_name="中文名称", max_length=30)
    name_en = models.CharField(verbose_name="英文名称", max_length=30)
    tc3 = models.ForeignKey(
        TC3,
        verbose_name="TC III",
        on_delete=models.CASCADE,
        related_name="tc3_tc4s",
    )

    class Meta:
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} {self.name_cn}|{self.name_en}"


class Molecule(models.Model):
    name_cn = models.CharField(verbose_name="中文名称", max_length=50)
    name_en = models.CharField(verbose_name="英文名称", max_length=50)
    tc4 = models.ForeignKey(
        TC4,
        verbose_name="TC IV",
        on_delete=models.CASCADE,
        related_name="tc4_molecules",
    )

    class Meta:
        verbose_name = "通用名"
        verbose_name_plural = "通用名"
        ordering = ["name_cn"]

    def __str__(self) -> str:
        return f"{self.name_cn}|{self.name_en}"


class Company(models.Model):
    full_name = models.CharField(max_length=100, verbose_name="企业全称", unique=True)
    abbr_name = models.CharField(max_length=50, verbose_name="企业简称")
    mnc_or_local = models.BooleanField(verbose_name="是否跨国企业")

    class Meta:
        verbose_name = "制药企业"
        verbose_name_plural = "制药企业"
        ordering = ["abbr_name", "full_name"]

    def __str__(self) -> str:
        return f"{self.abbr_name} ({self.full_name})"


class Subject(models.Model):
    name = formulation = models.CharField(verbose_name="名称", max_length=50)
    molecule = models.ForeignKey(
        Molecule,
        verbose_name="通用名",
        on_delete=models.CASCADE,
        related_name="molecule_subjects",
    )
    formulation = models.CharField(verbose_name="剂型", max_length=20)
    therapy_class = models.CharField(verbose_name="治疗领域", max_length=20)
    origin_company = models.ForeignKey(
        Company,
        verbose_name="原研公司",
        on_delete=models.CASCADE,
        related_name="company_subjects",
    )

    class Meta:
        verbose_name = "谈判主体"
        verbose_name_plural = "谈判主体"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.molecule__name_cn}|{self.molecule__name_en})"

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
    dosage_for_price = models.CharField(verbose_name="价格对应规格", max_length=100)
    note = models.TextField(verbose_name="备注", blank=True, null=True)

    class Meta:
        verbose_name = "医保谈判"
        verbose_name_plural = "医保谈判"
        ordering = ["subject__molecule__name_cn", "nego_date"]

    def __str__(self) -> str:
        return f"{self.subject__molecule__name_cn} ({self.year})"

    @property
    def year(self) -> int:
        return int(self.date.year)

    @property
    def price_change(self) -> Optional[float]:
        try:
            change = self.price_new / self.price_old - 1
        except:
            change = np.nan
        return change
