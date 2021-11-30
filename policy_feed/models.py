from django.db import models
import time


class Announce(models.Model):
    title = models.CharField(verbose_name="公告标题", max_length=300)
    url = models.CharField(verbose_name="公告链接", max_length=300)
    source = models.CharField(verbose_name="来源", max_length=30)
    pub_date = models.DateField(verbose_name="发布日期")
    fetch_date = models.DateField(verbose_name="爬取日期")
    region = models.CharField(verbose_name="区域", max_length=10)
    
    class Meta:
        verbose_name = "政策公告"
        verbose_name_plural = "政策公告"
        ordering = ["-pub_date", "source", "title", "url"]

    def __str__(self):
        return "%s %s %s %s" % (self.pub_date, self.source, self.title, self.url)

