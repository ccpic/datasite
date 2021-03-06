from django.urls import include, path
from . import views
# from rest_framework import routers

# router = routers.DefaultRouter()
# router.register(r'records', views.RecordViewSet)
# router.register(r'tenders', views.TenderViewSet)

app_name = 'medical_info'
urlpatterns = [
    path('', views.index, name='index'),
    path(r'posts/<slug:slug>', views.post_detail, name='post_detail'), # 文章详情页
    path(r'posts_mail_format/<slug:slug>', views.post_mail_format, name='post_mail_format'), # 适合导出到邮件的文章格式
    path(r'tags/<int:pk>', views.tagged, name='tagged'), # 指定标签相关的文章
    path(r'programs/<int:pk>', views.program, name='program'), # 指定栏目的文章
    path(r'search', views.search, name='search'),
]