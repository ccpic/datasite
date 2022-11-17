from django.urls import include, path
from . import views

# from rest_framework import routers

# router = routers.DefaultRouter()
# router.register(r'records', views.RecordViewSet)
# router.register(r'tenders', views.TenderViewSet)

app_name = "kol"
urlpatterns = [
    path("", views.records, name="records"),
    path("kols", views.kols, name="kols"),
    path("create_kol", views.create_kol, name="create_kol"),
    path("update_kol/<int:pk>", views.update_kol, name="update_kol"),
    path("delete_kol", views.delete_kol, name="delete_kol"),
]
