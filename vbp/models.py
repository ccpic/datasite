from django.db import models
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Avg, Count, Min, Sum
from django.db.models.signals import m2m_changed
from django.db.models import Q, UniqueConstraint


REGION_CHOICES = [
    ("北京", "北京"),
    ("天津", "天津"),
    ("上海", "上海"),
    ("重庆", "重庆"),
    ("广州", "广州"),
    ("深圳", "深圳"),
    ("成都", "成都"),
    ("沈阳", "沈阳"),
    ("大连", "大连"),
    ("西安", "西安"),
    ("厦门", "厦门"),
    ("河北", "河北"),
    ("山西", "山西"),
    ("内蒙古", "内蒙古"),
    ("辽宁", "辽宁"),
    ("吉林", "吉林"),
    ("黑龙江", "黑龙江"),
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
    ("四川", "四川"),
    ("贵州", "贵州"),
    ("云南", "云南"),
    ("西藏", "西藏"),
    ("陕西", "陕西"),
    ("甘肃", "甘肃"),
    ("青海", "青海"),
    ("宁夏", "宁夏"),
    ("新疆（含兵团）", "新疆（含兵团）"),
]


#  规格换算系数
D_MAIN_SPEC = {
    "阿卡波糖口服常释剂型": {"50mg": 1, "100mg": 2,},
    "阿莫西林口服常释剂型": {"0.25g": 1, "0.5g": 2,},
    "阿奇霉素口服常释剂型": {"0.25g": 1, "0.5g": 2,},
    "安立生坦片": {"5mg": 1, "10mg": 2,},
    "奥美沙坦酯口服常释剂型": {"20mg": 1, "40mg": 2,},
    "比索洛尔口服常释剂型": {"2.5mg": 0.5, "5mg": 1,},
    "多奈哌齐口服常释剂型": {"5mg": 1, "10mg": 2},
    "氟康唑口服常释剂型": {"50mg": 1, "150mg": 3},
    "格列美脲口服常释剂型": {"1mg": 0.5, "2mg": 1,},
    "坎地沙坦酯口服常释剂型": {"4mg": 0.5, "8mg": 1},
    "克林霉素口服常释剂型": {"0.075g": 0.5, "0.15g": 1},
    "索利那新口服常释剂型": {"5mg": 1, "10mg": 2},
    "特拉唑嗪口服常释剂型": {"1mg": 0.5, "2mg": 1},
    "替吉奥口服常释剂型": {"20mg": 1, "25mg": 1.2},
    "头孢氨苄口服常释剂型": {"0.25g": 1, "0.5g": 2},
    "辛伐他汀口服常释剂型": {"20mg": 1, "40mg": 2},
    "异烟肼口服常释剂型": {"0.1g": 1, "0.3g": 3},
    "阿托伐他汀口服常释剂型": {"10mg": 0.5, "20mg": 1},
    "艾司西酞普兰口服常释剂型": {"5mg": 0.5, "10mg": 1, "20mg": 2},
    "奥氮平口服常释剂型": {"5mg": 0.5, "10mg": 1},
    "厄贝沙坦口服常释剂型": {"75mg": 1, "150mg": 2},
    "恩替卡韦口服常释剂型": {"0.5mg": 1, "1mg": 2},
    "赖诺普利口服常释剂型": {"5mg": 0.5, "10mg": 1},
    "利培酮口服常释剂型": {"1mg": 1, "3mg": 3},
    "氯吡格雷口服常释剂型": {"25mg": 1 / 3, "75mg": 1},
    "氯沙坦口服常释剂型": {"50mg": 1, "100mg": 2},
    "培美曲塞注射剂": {"100mg": 1, "500mg": 5},
    "瑞舒伐他汀口服常释剂型": {"5mg": 0.5, "10mg": 1},
    "依那普利口服常释剂型": {"5mg": 0.5, "10mg": 1, "100mg": 10},
    "氨基葡萄糖口服常释剂型": {"0.25g": 1, "0.75g": 3},
    "奥氮平口腔崩解片": {"5mg": 1, "10mg": 2},
    "奥美拉唑口服常释剂型": {"10mg": 1, "20mg": 2},
    "布洛芬颗粒剂": {"0.1g": 0.5, "0.2g": 1},
    "二甲双胍口服常释剂型": {"0.25g": 0.5, "0.5g": 1},
    "非布司他口服常释剂型": {"20mg": 0.5, "40mg": 1},
    "枸橼酸西地那非片": {"25mg": 0.5, "50mg": 1, "100mg": 2},
    "卡培他滨口服常释剂型": {"0.15g": 0.3, "0.5g": 1},
    "卡托普利口服常释剂型": {"12.5mg": 0.5, "25mg": 1},
    "喹硫平口服常释剂型": {"25mg": 0.25, "0.1g": 1, "0.2g": 2, "0.3g": 3},
    "拉米夫定口服常释剂型": {"0.15g": 0.5, "0.3g": 1},
    "孟鲁司特咀嚼片": {"4mg": 0.8, "5mg": 1},
    "匹伐他汀口服常释剂型": {"1mg": 0.5, "2mg": 1},
    "普芦卡必利口服常释剂型": {"1mg": 0.5, "2mg": 1},
    "缬沙坦口服常释剂型": {"40mg": 0.5, "80mg": 1, "160mg": 2},
    "盐酸达泊西汀片": {"30mg": 1, "60mg": 2},
    "依托考昔口服常释剂型": {"30mg": 0.5, "60mg": 1, "90mg": 1.5, "120mg": 2},
    "头孢克洛口服常释剂型": {"0.25g": 1, "0.5g": 2},
    "克拉霉素口服常释剂型": {"250mg": 1, "500mg": 2},
}


class Tender(models.Model):
    target = models.CharField(max_length=30, verbose_name="带量品种")
    vol = models.CharField(max_length=30, verbose_name="批次")
    ceiling_price = models.FloatField(verbose_name="报价最高限价")
    tender_begin = models.DateField(verbose_name="标期起始日期")

    class Meta:
        verbose_name = "集采标的"
        verbose_name_plural = "集采标的"
        ordering = ["target"]
        unique_together = ["target", "vol"]

    def __str__(self):
        return "%s %s" % (self.vol, self.target)

    @property
    def bidder_num(self):
        return self.bids.all().count()

    @property
    def winner_num(self):
        return self.winners().count()

    @property
    def proc_percentage(self):
        if self.target in [
            "阿莫西林颗粒剂",
            "利奈唑胺口服常释剂型",
            "莫西沙星氯化钠注射剂",
            "左氧氟沙星滴眼剂",
            "环丙沙星口服常释剂型",
            "头孢地尼口服常释剂型",
            "头孢克洛口服常释剂型",
            "克拉霉素口服常释剂型",
        ]:
            if self.winner_num == 1:
                pct = 0.4
            elif self.winner_num == 2:
                pct = 0.5
            elif self.winner_num == 3:
                pct = 0.6
            else:
                pct = 0.7
        else:
            if self.winner_num == 1:
                pct = 0.5
            elif self.winner_num == 2:
                pct = 0.6
            elif self.winner_num == 3:
                pct = 0.7
            else:
                pct = 0.8
        return pct

    def get_specs(self):  # 所有相关报量里出现的规格
        return (
            self.region_volume.all()
            .order_by("spec")
            .values_list("spec", flat=True)
            .distinct()
        )

    @property
    def main_spec(self):  # 区分主规格，字典里折算index为1的是主规格
        try:
            for spec in self.get_specs():
                if D_MAIN_SPEC[self.target][spec] == 1:
                    return spec
        except:
            return self.get_specs()[0]

    @property
    def specs_num(self):  # 规格数量
        return len(self.get_specs())

    def total_std_volume_reported(self):  # 计算报量总和
        if self.specs_num == 1:
            qs = self.region_volume.all()
            if qs.exists():
                volume = qs.aggregate(Sum("amount_reported"))["amount_reported__sum"]
                return volume
            else:
                return 0
        else:  # 如果不止一种规格要折算后再求和
            volume = 0
            for spec in self.get_specs():
                qs = self.region_volume.all().filter(spec=spec)
                if qs.exists():
                    volume += (
                        qs.aggregate(Sum("amount_reported"))["amount_reported__sum"]
                        * D_MAIN_SPEC[self.target][spec]
                    )
                else:
                    volume += 0
            return volume

    def total_std_volume_contract(self):  # 计算合同量总和
        return self.total_std_volume_reported() * self.proc_percentage

    def total_value_contract(self):  # 计算合同金额总和（根据中标价）
        value = 0
        for bid in self.bids.all():
            value += bid.value_win()
        return value

    def lowest_origin_price(self):
        qs = self.bids.exclude(original_price=None).order_by("original_price").first()
        if qs != 99999:
            try:
                return qs.original_price
            except:
                return None
        else:
            return None

    def first_winner_pricecut(self):
        qs = self.bids.order_by("bid_price").first()
        if qs != 99999:
            try:
                return qs.bid_price / self.lowest_origin_price() - 1
            except:
                return None
        else:
            return None

    @property
    def tender_period(self):
        if self.winner_num == 1:  # 1家中标，标期1年
            return 1
        elif 2 <= self.winner_num <= 3:
            return 2
        elif self.winner_num >= 4:
            return 3

    @property
    def tender_end(self):
        year = timedelta(days=365)  # 1年
        return self.tender_begin + self.tender_period * year

    # @property
    # def winner_num_max(self):
    #     if self.bidder_num == 1:  # 1家竞标，1家中标，下同
    #         return 1
    #     elif 2 <= self.bidder_num <= 3:
    #         return 2
    #     elif self.bidder_num == 4:
    #         return 3
    #     elif 5 <= self.bidder_num <= 6:
    #         return 4
    #     elif 7 <= self.bidder_num <= 8:
    #         return 5
    #     elif self.bidder_num > 8:
    #         return 6

    @property
    def regions(self):
        return (
            self.region_volume.all()
            .order_by("region")
            .values_list("region", flat=True)
            .distinct()
        )

    def winners(self):
        winner_ids = [bid.id for bid in self.bids.all() if bid.is_winner()]
        return self.bids.filter(id__in=winner_ids).order_by("bid_price")

    def get_lowest_original_price(self):
        qs = self.bids.all().exclude(original_price=None).order_by("original_price")
        if qs.exists():
            return qs.first().original_price
        else:
            return None


class Company(models.Model):
    full_name = models.CharField(max_length=100, verbose_name="企业全称", unique=True)
    abbr_name = models.CharField(max_length=50, verbose_name="企业简称")
    mnc_or_local = models.BooleanField(verbose_name="是否跨国企业")

    class Meta:
        verbose_name = "制药企业"
        verbose_name_plural = "制药企业"
        ordering = ["abbr_name", "full_name"]

    def __str__(self):
        return "%s (%s)" % (self.abbr_name, self.full_name)


class Bid(models.Model):
    tender = models.ForeignKey(
        Tender, on_delete=models.CASCADE, verbose_name="所属记录", related_name="bids"
    )
    bidder = models.ForeignKey(
        Company, on_delete=models.CASCADE, verbose_name="竞标厂商", related_name="bids"
    )
    origin = models.BooleanField(verbose_name="是否该标的原研")
    bid_price = models.FloatField(verbose_name="报价")
    original_price = models.FloatField(verbose_name="集采前最低价", blank=True, null=True)

    class Meta:
        verbose_name = "投标记录"
        verbose_name_plural = "投标记录"
        ordering = ["-bid_price"]
        unique_together = (("tender", "bidder"),)

    def __str__(self):
        return "%s %s %s" % (self.tender.__str__(), self.bidder, self.bid_price)

    def is_winner(self):  # 该bid是否中标
        qs = self.region_volume.all()
        if qs.exists():
            return True
        else:
            return False

    def price_cut(self):  # 相比集采前降价幅度
        if self.bid_price != 99999:
            try:
                return self.bid_price / self.original_price - 1
            except:
                return None
        else:
            return None

    def price_cut_to_ceiling(self):  # 相比最高限价降价幅度
        if self.bid_price != 99999:
            try:
                return self.bid_price / self.tender.ceiling_price - 1
            except:
                return None
        else:
            return None

    def price_cut_to_lowest(self):  # 相比集采前降价幅度
        if self.bid_price != 99999:
            try:
                return self.bid_price / self.tender.get_lowest_original_price() - 1
            except:
                return None
        else:
            return None

    def regions_win(self):
        return (
            self.region_volume.all()
            .order_by("region")
            .values_list("region", flat=True)
            .distinct()
        )

    def std_volume_win(self, spec=None, region=None):
        if spec is not None and region is not None:
            qs = self.region_volume.filter(spec=spec, region=region)
            if qs.exists():
                volume = qs[0].amount_reported
                volume = volume * self.tender.proc_percentage
            else:
                volume = 0
        elif spec is not None and region is None:
            qs = self.region_volume.filter(spec=spec)
            if qs.exists():
                volume = qs.aggregate(Sum("amount_reported"))["amount_reported__sum"]
                volume = volume * self.tender.proc_percentage
            else:
                volume = 0
        elif spec is None and region is not None:
            if self.tender.specs_num == 1:
                qs = self.region_volume.filter(region=region)
                if qs.exists():
                    volume = qs.aggregate(Sum("amount_reported"))[
                        "amount_reported__sum"
                    ]
                    volume = volume * self.tender.proc_percentage
                else:
                    volume = 0
            else:
                volume = 0
                for spec in self.tender.get_specs():
                    qs = self.region_volume.filter(spec=spec, region=region)
                    if qs.exists():
                        volume += (
                            qs.aggregate(Sum("amount_reported"))["amount_reported__sum"]
                            * D_MAIN_SPEC[self.tender.target][spec]
                        )
                    else:
                        volume += 0
                volume = volume * self.tender.proc_percentage
        else:
            if self.tender.specs_num == 1:
                qs = self.region_volume.all()
                if qs.exists():
                    volume = qs.aggregate(Sum("amount_reported"))[
                        "amount_reported__sum"
                    ]
                    volume = volume * self.tender.proc_percentage
                else:
                    volume = 0
            else:
                volume = 0
                for spec in self.tender.get_specs():
                    qs = self.region_volume.all().filter(spec=spec)
                    if qs.exists():
                        volume += (
                            qs.aggregate(Sum("amount_reported"))["amount_reported__sum"]
                            * D_MAIN_SPEC[self.tender.target][spec]
                        )
                    else:
                        volume += 0
                volume = volume * self.tender.proc_percentage
        return volume

    def value_win(self):
        return self.std_volume_win() * self.bid_price

    def clean(self):
        try:
            bid_num = self.tender.bids.exclude(pk=self.pk).count()
            bid_allowed_num = self.tender.bidder_num
            if bid_num >= bid_allowed_num:
                raise ValidationError(
                    "同一记录下竞标数量%s家已达到标的允许的%s家" % (bid_num, bid_allowed_num)
                )
        except ObjectDoesNotExist:
            pass

        try:
            if (
                self.tender.bids.filter(origin=True).exclude(pk=self.pk).count() > 0
                and self.origin is True
            ):  # 只能有1家原研
                raise ValidationError("同一记录下最多只能有1家原研")
        except ObjectDoesNotExist:
            pass


class Volume(models.Model):
    tender = models.ForeignKey(
        Tender,
        on_delete=models.CASCADE,
        verbose_name="标的",
        related_name="region_volume",
    )
    region = models.CharField(max_length=10, choices=REGION_CHOICES, verbose_name="区域")
    spec = models.CharField(max_length=30, verbose_name="规格")
    amount_reported = models.FloatField(verbose_name="合同量")
    winner = models.ForeignKey(
        Bid,
        on_delete=models.CASCADE,
        verbose_name="中标供应商",
        blank=True,
        null=True,
        related_name="region_volume",
    )

    class Meta:
        verbose_name = "地方报量"
        verbose_name_plural = "地方报量"
        ordering = ["tender", "region", "spec"]

    def __str__(self):
        return "%s %s %s %s" % (
            self.tender.target,
            self.region,
            self.spec,
            self.amount_reported,
        )

    def amount_contract(self):
        return self.amount_reported * self.tender.proc_percentage


# def bids_changed(sender, **kwargs):
#     bid_num = kwargs['instance'].bid.count()
#     bid_allowed_num = kwargs['instance'].tender.bidder_num
#     if bid_num > bid_allowed_num :
#         raise ValidationError("竞标数%s家超过标的允许的%s家" % (bid_num, bid_allowed_num))
#
# m2m_changed.connect(bids_changed, sender=Record.bid.through)
