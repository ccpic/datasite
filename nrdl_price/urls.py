from django.urls import include, path

from . import views

app_name = "nrdl_price"
urlpatterns = [
    path("index", views.index, name="index"),
]
