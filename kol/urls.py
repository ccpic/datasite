from django.urls import include, path
from . import views
# from rest_framework import routers

# router = routers.DefaultRouter()
# router.register(r'records', views.RecordViewSet)
# router.register(r'tenders', views.TenderViewSet)

app_name = 'kol'
urlpatterns = [
    path('', views.records, name='records'),
    path('kols', views.kols, name='kols'),
    path('add_kol', views.add_kol, name='add_kol'),
]