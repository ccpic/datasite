from django.contrib import admin
from .models import *


class DrugAdmin(admin.ModelAdmin):
    search_fields = ("product_name_cn", "product_name_en", "molecule_cn", "molecule_en")


admin.site.register(
    Drug, DrugAdmin,
)
admin.site.register(
    [Company, Sales, TC_I, TC_II, TC_III]
)
