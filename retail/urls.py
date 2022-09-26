from django.urls import path
from . import views

app_name = 'retail'
urlpatterns = [
    path('', views.index, name='index'),
    path(r'query', views.query, name='query'),  # 主查询AJAX URL
]