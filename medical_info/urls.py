from django.urls import include, path
from . import views
# from rest_framework import routers

# router = routers.DefaultRouter()
# router.register(r'records', views.RecordViewSet)
# router.register(r'tenders', views.TenderViewSet)

app_name = 'medical_info'
urlpatterns = [
    path('', views.posts, name='posts'),
    path(r'posts/<int:pk>', views.post_detail, name='post_detail'), # 文章详情页
    path(r'posts_mail_format/<int:pk>', views.post_mail_format, name='post_mail_format'), # 适合导出到邮件的文章格式
]