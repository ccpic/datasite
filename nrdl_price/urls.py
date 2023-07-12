from django.urls import include, path

from . import views

app_name = "kol"
urlpatterns = [
    path("index", views.index, name="index"),
]
