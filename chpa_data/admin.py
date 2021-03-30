from django.contrib import admin
from .models import *


admin.site.register(
    [
        viz_type,
        defined_market,
        TC_I,
        TC_II,
        TC_III,
        TC_IV,
        Molecule,
        Product,
        Package,
        Corporation,
        Manuf_type,
        Formulation,
        Strength,
        Molecule_TC,
        Product_Corp,
    ]
)

