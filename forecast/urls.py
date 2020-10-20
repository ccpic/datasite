from django.urls import path
from . import views

app_name = 'forecast'
urlpatterns = [
    path('', views.index, name='index'),
    path(r'ajax_process/', views.ajax_process, name='ajax_process'),
]