from django.urls import path
from . import views

app_name = "nrdl_renewal"
urlpatterns = [
    path("", views.index, name="index"),
    path(r"general_catalog/", views.general_catalog, name="general_catalog"),
    path(r"if_simple/", views.if_simple, name="if_simple"),
    path(r"price_cut/", views.price_cut, name="price_cut"),
]
