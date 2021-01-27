from django.db import models


class Province(models.Model):
    name = models.CharField(max_length=3)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        verbose_name_plural = "Cities"

    def __str__(self):
        return self.name


class County(models.Model):
    name = models.CharField(max_length=30)

    class Meta:
        verbose_name_plural = "Counties"

    def __str__(self):
        return self.name


class Hospital(models.Model):
    name = models.CharField(max_length=110)

    def __str__(self):
        return self.name


class Level(models.Model):
    name = models.CharField(max_length=4)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class BU(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class RD(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name


class RM_POS_NAME(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class DSM_POS_NAME(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class RSP_POS_NAME(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name
