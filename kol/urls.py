from django.urls import include, path

from . import views

# from rest_framework import routers

# router = routers.DefaultRouter()
# router.register(r'records', views.RecordViewSet)
# router.register(r'tenders', views.TenderViewSet)

app_name = "kol"
urlpatterns = [
    path("records", views.records, name="records"),
    path("kols", views.kols, name="kols"),
    path("kols/create", views.create_kol, name="create_kol"),
    path("kols/<int:pk>/update", views.update_kol, name="update_kol"),
    path("kols/delete_kol", views.delete_kol, name="delete_kol"),
    path("kols/export_kol", views.export_kol, name="export_kol"),
    path("records/create", views.create_record, name="create_record"),
    path("records/<int:pk>/update", views.update_record, name="update_record"),
    path("records/delete_record", views.delete_record, name="delete_record"),
    path("records/export", views.export_record, name="export_record"),
    path(r"search_hps/<str:kw>", views.search_hps, name="search_hps"),
]
