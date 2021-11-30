from django.urls import include, path
from . import views


app_name = 'policy_feed'
urlpatterns = [
    path('', views.feeds, name='feeds'),
]