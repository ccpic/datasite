from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q, UniqueConstraint

DEPT_CHOICES = [
    ("肾内科", "肾内科"),
    ("其他科室", "其他科室"),
]

RATING_CHOICES = [(3, "高"), (2, "中"), (1, "低")]


class Hospital(models.Model):
    xltid = models.CharField(verbose_name="信立泰医院id", max_length=10, unique=True)
    name = models.CharField(verbose_name="医院名称", max_length=200, unique=True)
    province = models.CharField(max_length=10, verbose_name="省/自治区/直辖市")
    city = models.CharField(max_length=20, verbose_name="城市")
    decile = models.IntegerField(verbose_name="医院潜力分级")
    dsm = models.CharField(max_length=10, verbose_name="当前地区经理", null=True)

    class Meta:
        verbose_name = "医院"
        verbose_name_plural = "医院"
        ordering = ["name"]

    def __str__(self):
        return f"{self.province} {self.city} D{self.decile} {self.name}"


class Kol(models.Model):
    name = models.CharField(verbose_name="姓名", max_length=20)
    hospital = models.ForeignKey(
        Hospital,
        verbose_name="供职医院",
        on_delete=models.SET_NULL,
        null=True,
        related_name="kol_hospital",
    )
    dept = models.CharField(max_length=10, choices=DEPT_CHOICES, verbose_name="所在科室")
    rating_infl = models.IntegerField(choices=RATING_CHOICES, verbose_name="影响力")
    rating_prof = models.IntegerField(choices=RATING_CHOICES, verbose_name="专业度")
    titles = models.TextField(verbose_name="头衔&荣誉", blank=True, null=True)
    upload_date = models.DateTimeField(verbose_name="创建日期", default=timezone.now)
    pub_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="kol_pub_user"
    )

    class Meta:
        ordering = ["name"]
        constraints = [UniqueConstraint(fields=["name", "hospital"], name="unique kol")]

    def __str__(self):
        return f"{self.hospital} - {self.name}"


class Record(models.Model):
    kol = models.ForeignKey(
        Kol,
        on_delete=models.SET_NULL,
        verbose_name="KOL",
        null=True,
        related_name="record_kol",
    )
    visit_date = models.DateField(verbose_name="拜访日期")
    purpose = models.TextField(verbose_name="拜访目标")
    feedback_main = models.TextField(verbose_name="主要反馈")
    feedback_oth = models.TextField(verbose_name="其他重要信息")
    upload_date = models.DateTimeField(verbose_name="记录日期", default=timezone.now)
    pub_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="记录人",
        related_name="record_pub_user",
    )

    class Meta:
        verbose_name = "拜访记录"
        verbose_name_plural = "拜访记录"
        ordering = ["-visit_date"]

    def __str__(self):
        return f"{self.visit_date} - {self.kol}"
