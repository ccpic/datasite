from django.urls import include, path

from . import views

app_name = "nrdl_price"
urlpatterns = [
    path(r"", views.subjects, name="subjects"),
    path(r"export", views.export, name="export"),
]
