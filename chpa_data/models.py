from django.db import models

class viz_type(models.Model):
    name = models.CharField(max_length=20)
    metric = models.CharField(max_length=20)
    chart_type = models.CharField(max_length=20)
    href = models.CharField(max_length=50)
    image_link = models.CharField(max_length=20)
    position = models.IntegerField()

    class Meta:
        ordering = ('position',)

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
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Package(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Corporation(models.Model):
    name = models.CharField(max_length=200)

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