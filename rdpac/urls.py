from django.urls import path
from . import views

app_name = "rdpac"
urlpatterns = [
    path("", views.index, name="index"),
    path(r"drug/<int:pk>", views.drug_detail, name="drug_detail"),  # 药品详情页
    path(r"company/<int:pk>", views.company_detail, name="company_detail"),  # 药品详情页
]
