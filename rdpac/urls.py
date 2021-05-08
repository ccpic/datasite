from django.urls import path
from . import views

app_name = "rdpac"
urlpatterns = [
    path("", views.index, name="index"),
    path(r"drug/", views.drug, name="drug"),  # 药品列表
    path(r"drug/<int:drug_id>", views.drug_detail, name="drug_detail"),  # 药品详情页
    path(r"company/", views.company, name="company"),  # 公司列表
    path(
        r"company/<int:company_id>", views.company_detail, name="company_detail"
    ),  # 公司详情页
    path(r"tc_iii/", views.tc_iii, name="tc_iii"),  # TC3列表
    path(r"search/<str:kw>", views.search, name="search"),  # 搜索
]
