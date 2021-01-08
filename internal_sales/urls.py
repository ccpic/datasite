from django.urls import path
from . import views

app_name = 'internal_sales'
urlpatterns = [
    path('', views.index, name='index'),
    path(r'query', views.query, name='query'),  # 主查询AJAX URL
    path(r'search/<str:column>/<str:kw>', views.search, name='search'),  # 表单备选项搜索URL
]