from django.urls import path
from . import views

app_name = 'internal_sales'
urlpatterns = [
    path('', views.index, name='index'),
]