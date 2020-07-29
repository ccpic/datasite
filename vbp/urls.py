from django.urls import include, path
from . import views
# from rest_framework import routers

# router = routers.DefaultRouter()
# router.register(r'records', views.RecordViewSet)
# router.register(r'tenders', views.TenderViewSet)

app_name = 'vbp'
urlpatterns = [
    path('', views.index, name='index'),
    path(r'bids/<int:bid_id>',  views.bid_detail, name='bid_detail'),
    path(r'tenders/<int:tender_id>', views.tender_detail, name='tender_detail'),
    path(r'companies/<int:company_id>', views.company_detail, name='company_detail'),
    path(r'search', views.search, name='search'),
    path(r'analysis', views.analysis, name='analysis'),
    path(r'export', views.export, name='export')
    # path('', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]