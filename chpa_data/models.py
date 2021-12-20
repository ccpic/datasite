from django.db import models
from django.conf import settings
from picklefield.fields import PickledObjectField

class Record(models.Model):
    args = PickledObjectField(verbose_name="查询参数", null=True, blank=True)
    sql = models.CharField(max_length=1024, verbose_name="SQL语句")
    is_fav = models.BooleanField(verbose_name="是否收藏")
    fav_name = models.CharField(max_length=30, verbose_name="收藏名称", null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="用户")
    query_date = models.DateTimeField(verbose_name='查询日期',auto_now=True)

    class Meta:
        verbose_name = '查询记录'
        verbose_name_plural = '查询记录'
        ordering = ['-query_date']

    def __str__(self):
        return self.query_date.strftime('%Y年%m月%d日')

    def args_unpacked(self):
        return u'{args}'.format(args=self.args)


class viz_type(models.Model):
    name = models.CharField(max_length=20)
    metric = models.CharField(max_length=20)
    chart_type = models.CharField(max_length=20)
    href = models.CharField(max_length=50)
    image_link = models.CharField(max_length=20)
    position = models.IntegerField()

    class Meta:
        ordering = ("position",)

    def __str__(self):
        return self.name


class defined_market(models.Model):
    name = models.CharField(max_length=50)
    definition = models.CharField(max_length=50)
    db_table = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class TC_I(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class TC_II(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class TC_III(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class TC_IV(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Molecule(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name


class Package(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name


class Corporation(models.Model):
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name


class Manuf_type(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Formulation(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Strength(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Molecule_TC(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Product_Corp(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
