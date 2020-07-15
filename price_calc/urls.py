from django.urls import path
from . import views

app_name = 'price_calc'
urlpatterns = [
    path('', views.index, name='index'),
    path(r'ajax_calc/', views.ajax_calc, name='ajax_calc'),
]