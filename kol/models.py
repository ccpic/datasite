from django.db import models


DEPT_CHOICES = [
    ("肾内科", "肾内科"),
    ("其他科室", "其他科室"),
]


DECILE_CHOICES = [
    ("D10", "D10"),
    ("D9", "D9"),
    ("D8", "D8"),
    ("D7", "D7"),
    ("D6", "D6"),
    ("D5", "D5"),
    ("D4", "D4"),
    ("D3", "D3"),
    ("D2", "D2"),
    ("D1", "D1"),
]

PROVINCE_CHOICES = [
    ("北京", "北京"),
    ("天津", "天津"),
    ("河北", "河北"),
    ("山西", "山西"),
    ("内蒙古", "内蒙古"),
    ("辽宁", "辽宁"),
    ("吉林", "吉林"),
    ("黑龙江", "黑龙江"),
    ("上海", "上海"),
    ("江苏", "江苏"),
    ("浙江", "浙江"),
    ("安徽", "安徽"),
    ("福建", "福建"),
    ("江西", "江西"),
    ("山东", "山东"),
    ("河南", "河南"),
    ("湖北", "湖北"),
    ("湖南", "湖南"),
    ("广东", "广东"),
    ("广西", "广西"),
    ("海南", "海南"),
    ("重庆", "重庆"),
    ("四川", "四川"),
    ("贵州", "贵州"),
    ("云南", "云南"),
    ("西藏", "西藏"),
    ("陕西", "陕西"),
    ("甘肃", "甘肃"),
    ("青海", "青海"),
    ("宁夏", "宁夏"),
    ("新疆", "新疆"),
]

RATING_CHOICES = [(3, "高"), (2, "中"), (1, "低")]


class Hospital(models.Model):
    xltid = models.CharField(verbose_name="信立泰医院id", max_length=10, unique=True)
    name = models.CharField(verbose_name="医院名称", max_length=200, unique=True)
    province = models.CharField(
        max_length=10, choices=PROVINCE_CHOICES, verbose_name="省/自治区/直辖市"
    )
    decile = models.CharField(
        max_length=3, choices=DECILE_CHOICES, verbose_name="医院潜力分级"
    )

    class Meta:
        verbose_name = "医院"
        verbose_name_plural = "医院"
        ordering = ["name"]

    def __str__(self):
        return f"{self.province} {self.decile} {self.name}"


class Kol(models.Model):
    name = models.CharField(verbose_name="姓名", max_length=20)
    hospital = models.ForeignKey(
        Hospital, verbose_name="供职医院", on_delete=models.SET_NULL, null=True
    )
    dept = models.CharField(max_length=10, choices=DEPT_CHOICES, verbose_name="所在科室")
    rating_infl = models.IntegerField(choices=RATING_CHOICES, verbose_name="影响力")
    rating_prof = models.IntegerField(choices=RATING_CHOICES, verbose_name="专业度")

    def __str__(self):
        return f"{self.hospital} - {self.name}"
