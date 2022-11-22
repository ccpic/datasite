from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q, UniqueConstraint
import os

DEPT_CHOICES = [
    ("肾内科", "肾内科"),
    ("其他科室", "其他科室"),
]

RATING_CHOICES = [(4, 4), (3, 3), (2, 2), (1, 1)]


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
        related_name="hospital_kols",
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
    RATING_AWARENESS_CHOICES = [
        (3, "3_应用并熟悉产品特性"),
        (2, "2_已开始应用"),
        (1, "1_了解但未应用"),
        (0, "0_不了解"),
    ]
    RATING_EFFICACY_CHOICES = [
        (3, "3_Hb改善与罗沙司他类似，稳定性更好"),
        (2, "2_Hb改善与罗沙司他类似"),
        (1, "1_不了解"),
        (0, "0_Hb改善不如罗沙司他"),
    ]
    RATING_SAFETY_CHOICES = [
        (3, "3_较罗沙司他更安全"),
        (2, "2_与罗沙司他无差别"),
        (1, "1_不了解"),
        (0, "0_不及罗沙司他安全"),
    ]
    RATING_COMPLIANCE_CHOICES = [
        (3, "3_与罗沙司他比较，医嘱更方便"),
        (2, "2_与罗沙司他无差别"),
        (1, "1_不了解"),
        (0, "0_不如罗沙司他用药方便"),
    ]
    kol = models.ForeignKey(
        Kol,
        on_delete=models.SET_NULL,
        verbose_name="KOL",
        null=True,
        related_name="kol_records",
    )
    visit_date = models.DateField(verbose_name="拜访日期")
    purpose = models.TextField(verbose_name="拜访目标")
    # rating_favor = models.IntegerField(choices=RATING_CHOICES, verbose_name="恩那度司他支持度")
    rating_awareness = models.IntegerField(
        choices=RATING_AWARENESS_CHOICES, verbose_name="恩那度司他认知度"
    )
    rating_efficacy = models.IntegerField(
        choices=RATING_EFFICACY_CHOICES, verbose_name="恩那度司他疗效"
    )
    rating_safety = models.IntegerField(
        choices=RATING_SAFETY_CHOICES, verbose_name="恩那度司他安全性"
    )
    rating_compliance = models.IntegerField(
        choices=RATING_COMPLIANCE_CHOICES, verbose_name="恩那度司他便捷性"
    )
    feedback = models.TextField(verbose_name="主要反馈及其他重要信息")
    upload_date = models.DateTimeField(verbose_name="记录日期", default=timezone.now)
    pub_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="记录人",
        related_name="pub_user_records",
    )

    class Meta:
        verbose_name = "拜访记录"
        verbose_name_plural = "拜访记录"
        ordering = ["-visit_date"]

    def __str__(self):
        return f"{self.visit_date} - {self.kol}"


def get_filename(instance, filename):
    record_id = instance.record.pk
    return "kol/%s-%s" % (record_id, filename)


class Attachment(models.Model):
    record = models.ForeignKey(
        Record,
        on_delete=models.CASCADE,
        default=None,
        related_name="record_attachments",
    )
    file = models.FileField(upload_to=get_filename, verbose_name="文件")

    class Meta:
        verbose_name = "上传附件"
        verbose_name_plural = "上传附件"

    def __str__(self):
        return os.path.basename(self.file.name)

    def filename(self):
        return os.path.basename(self.file.name)
