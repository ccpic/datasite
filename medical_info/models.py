from django.db import models
from django.db.models.base import Model
from taggit.managers import TaggableManager
from uuslug import slugify
import os
import datetime
from django.core.validators import MaxValueValidator, MinValueValidator


def get_filename(instance, filename):
    slug = instance.post.url_slug
    return "medical_info/%s-%s" % (slug, filename)


def slugify_max(text, max_length=50):
    slug = slugify(text)
    if len(slug) <= max_length:
        return slug
    trimmed_slug = slug[:max_length].rsplit("-", 1)[0]
    if len(trimmed_slug) <= max_length:
        return trimmed_slug
    # First word is > max_length chars, so we have to break it
    return slug[:max_length]


def current_year():
    return datetime.date.today().year


def max_value_current_year(value):
    return MaxValueValidator(current_year())(value)


class Nation(models.Model):
    name = models.CharField(verbose_name="国家名称", max_length=50)
    code = models.CharField(verbose_name="国家代码（用以匹配国旗）参考https://semantic-ui.com/elements/flag.html", max_length=50)  # 用以匹配国旗

    class Meta:
        verbose_name = "国家代码"
        verbose_name_plural = "国家代码"
        ordering = ["name"]

    def __str__(self):
        return "%s (%s)" % (self.name, self.code)

class PubAgent(models.Model):
    full_name = models.CharField(verbose_name="全称", max_length=200)
    abbr_name = models.CharField(verbose_name="简称", max_length=100)

    class Meta:
        verbose_name = "发布平台"
        verbose_name_plural = "发布平台"
        ordering = ["abbr_name"]

    def __str__(self):
        return "%s (%s)" % (self.abbr_name, self.full_name)


class Program(models.Model):
    name = models.CharField(verbose_name="名称", max_length=50)
    year = models.IntegerField(
        verbose_name="年份", validators=[MinValueValidator(2020), max_value_current_year]
    )
    vol = models.CharField(verbose_name="期数", max_length=50, blank=True, null=True)

    class Meta:
        verbose_name = "发布栏目"
        verbose_name_plural = "发布栏目"

    def __str__(self):
        return "%s %s (%s)" % (self.year, self.name, self.vol)


class Post(models.Model):
    title_en = models.CharField(verbose_name="英文标题", max_length=300)
    title_cn = models.CharField(verbose_name="中文标题", max_length=300)
    pub_agent = models.ForeignKey(
        PubAgent,
        on_delete=models.CASCADE,
        verbose_name="发布方",
        related_name="pub_agents",
    )
    pub_date = models.DateField(verbose_name="发布日期")
    pub_identifier = models.CharField(verbose_name="识别码", max_length=100)
    nation = models.ManyToManyField(to=Nation, verbose_name="涉及国家", blank=True)
    abstract = models.TextField(verbose_name="摘要")
    link = models.CharField(verbose_name="原平台链接", max_length=100)
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        default=None,
        verbose_name="栏目",
        null=True,
        blank=True,
        related_name="programs",
    )
    upload_date = models.DateTimeField(verbose_name="上传日期", auto_now=True)
    url_slug = models.SlugField(editable=False)
    tags = TaggableManager()
    views = models.IntegerField(verbose_name="阅读量", default=0)

    class Meta:
        verbose_name = "医学信息"
        verbose_name_plural = "医学信息"
        ordering = ["-upload_date"]

    def __str__(self):
        return "%s %s" % (self.title_cn, self.title_en)

    def save(self, *args, **kwargs):
        if self.title_en != "":
            self.url_slug = slugify_max(self.title_en)
        else:
            self.url_slug = slugify_max(self.title_cn)
        super(Post, self).save(*args, **kwargs)


class Images(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, default=None, related_name="images"
    )
    image = models.ImageField(upload_to=get_filename, verbose_name="图片")

    class Meta:
        verbose_name = "上传图片"
        verbose_name_plural = "上传图片"

    def __str__(self):
        return os.path.basename(self.image.name)

    def imagename(self):
        return os.path.basename(self.image.name)


class Files(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, default=None, related_name="files"
    )
    file = models.FileField(upload_to=get_filename, verbose_name="文件")

    class Meta:
        verbose_name = "内容文件"
        verbose_name_plural = "内容文件"

    def __str__(self):
        return os.path.basename(self.file.name)

    def filename(self):
        return os.path.basename(self.file.name)
