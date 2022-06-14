from django.urls import path
from . import views

app_name = "roxa"
urlpatterns = [
    path("", views.index, name="index"),
    path("province/", views.province, name="province"),
    path("city/", views.city, name="city"),
    path(r"query", views.query, name="query"),  # 主查询AJAX URL
    path(r"table_kpi", views.table_kpi, name="table_kpi"),  # 前端KPI表格服务器端加载AJAX URL
    # path(r"export/<str:type>", views.export, name="export"),  # 导出原始数URLs
    # path(r"table_hp", views.table_hp, name="table_hp"),  # 前端单家终端表格服务器端加载AJAX URL
    # # path(r'table_pivot', views.table_pivot, name='table_pivot'),  # 前端透视表格服务器端加载AJAX URL
    # path(r"export/<str:type>", views.export, name="export"),  # 导出原始数URL
    # # path(r'search/<str:column>/<str:kw>', views.search, name='search'),  # 表单备选项搜索URL
    # path(
    #     r"scatter_data", views.scatter_data, name="scatter_data"
    # ),  # AJAX异步加载单家终端潜力 versus 销量散点图
]
