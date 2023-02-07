import os

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q, UniqueConstraint
from django.utils import timezone

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
    SUPERVISOR_CHOICES = [
        ("博士生导师", "博士生导师"),
        ("硕士生导师", "硕士生导师"),
        ("非博导/硕导", "非博导/硕导"),
        ("未知", "未知"),
    ]
    CLASSFICATION_CHOICES = [
        ("学术型", "学术型"),
        ("临床型", "临床型"),
        ("未分型", "未分型"),
    ]
    name = models.CharField(verbose_name="姓名", max_length=20)
    hospital = models.ForeignKey(
        Hospital,
        verbose_name="供职医院",
        on_delete=models.SET_NULL,
        null=True,
        related_name="hospital_kols",
    )
    # dept = models.CharField(max_length=10, choices=DEPT_CHOICES, verbose_name="所在科室")
    rating_infl = models.IntegerField(choices=RATING_CHOICES, verbose_name="影响力")
    rating_prof = models.IntegerField(choices=RATING_CHOICES, verbose_name="专业度")
    rating_fav = models.IntegerField(choices=RATING_CHOICES, verbose_name="支持度")
    supervisor = models.CharField(
        choices=SUPERVISOR_CHOICES, verbose_name="是否博导/硕导", max_length=10
    )
    titles = models.TextField(verbose_name="头衔&荣誉", blank=True, null=True)
    classification = models.CharField(
        choices=CLASSFICATION_CHOICES, verbose_name="客户分型", max_length=3
    )
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
    ATTITUDE_1_CHOICES = [
        (3, "3_HIF-PHI在疗效保证前提下，刺激产生内源性EPO越接近生理浓度越好"),
        (2, "2_HIF-PHI在疗效保证前提下，EPO浓度无所谓"),
        (1, "1_HIF-PHI治疗，内源性EPO越高，疗效会越好"),
        (0, "0_本次拜访未涉及"),
    ]
    ATTITUDE_2_CHOICES = [
        (3, "3_Hb升速需适中，1-2g/dl最佳"),
        (2, "2_Hb升速慢点无所谓"),
        (1, "1_Hb需尽快达标，每月＞2g/dl危害不大"),
        (0, "0_本次拜访未涉及"),
    ]
    ATTITUDE_3_CHOICES = [
        (3, "3_选择性抑制PHD1及PHD3更高的HIF-PHI，更有利于HIF2α稳定，改善铁代谢更好"),
        (2, "2_不了解铁代谢与PHD不同亚型作用的相关性"),
        (1, "1_铁代谢与PHD不同亚型作用无相关性"),
        (0, "0_本次拜访未涉及"),
    ]
    ATTITUDE_4_CHOICES = [
        (3, "3_Hb升速波动过大会增加血栓事件风险"),
        (2, "2_不清楚Hb升速波动与血栓事件相关性"),
        (1, "1_Hb升速波动过大与血栓事件无相关性"),
        (0, "0_本次拜访未涉及"),
    ]
    ATTITUDE_5_CHOICES = [
        (3, "3_HIF-PHI对脂代谢的影响是“脱靶效应”的表现，HIF应更聚焦于红细胞生成"),
        (2, "2_不清楚HIF-PHI对脂代谢的改变对患者的远期影响"),
        (1, "1_HIF-PHI对脂代谢的影响是对患者的获益"),
        (0, "0_本次拜访未涉及"),
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
    attitude_1 = models.IntegerField(
        choices=ATTITUDE_1_CHOICES, verbose_name="治疗观念_HIF_PHI机制方面"
    )
    attitude_2 = models.IntegerField(
        choices=ATTITUDE_2_CHOICES, verbose_name="治疗观念_Hb升速稳定性"
    )
    attitude_3 = models.IntegerField(
        choices=ATTITUDE_3_CHOICES, verbose_name="治疗观念_铁代谢调节异质性"
    )
    attitude_4 = models.IntegerField(
        choices=ATTITUDE_4_CHOICES, verbose_name="治疗观念_升速与血栓事件关系"
    )
    attitude_5 = models.IntegerField(
        choices=ATTITUDE_5_CHOICES, verbose_name="治疗观念_脱靶效应相关"
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
