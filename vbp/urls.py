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
    path(r'search', views.search, name='search'), # 搜索功能
    path(r'gantt', views.gantt, name='gantt'), # 甘特图
    path(r'analysis', views.analysis, name='analysis'), # 分析功能
    path(r'docs', views.docs, name='docs'), # 集采官方文档展示页面
    path(r'export/<str:mode>/', views.export, name='export'),   # 导出全部
    path(r'export/<str:mode>/<str:tender_ids>', views.export, name='export')   # 导出指定记录
    # path('', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]