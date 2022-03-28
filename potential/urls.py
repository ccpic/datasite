from django.urls import path
from . import views

app_name = 'potential'
urlpatterns = [
    path('', views.index, name='index'),
    path(r'query', views.query, name='query'),  # 主查询AJAX URL
    path(r'table_hp', views.table_hp, name='table_hp'),  # 前端单家医院表格服务器端加载AJAX URL
    # path(r'table_pivot', views.table_pivot, name='table_pivot'),  # 前端透视表格服务器端加载AJAX URL
    path(r'export/<str:type>', views.export, name='export'),  # 导出原始数URL
    # path(r'search/<str:column>/<str:kw>', views.search, name='search'),  # 表单备选项搜索URL
]