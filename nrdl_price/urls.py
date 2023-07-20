from django.urls import include, path

from . import views

app_name = "nrdl_price"
urlpatterns = [
    path("negos", views.negos, name="negos"),
]
