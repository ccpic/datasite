"""
Docker 环境专用的 Django 设置文件
通过环境变量覆盖生产环境配置，无需修改原始 settings.py
"""
import os
from datasite.settings import *

# 从环境变量读取配置，如果没有则使用默认值（开发环境）
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# 数据库配置 - 从环境变量读取
DATABASES = {
    'default': {
        'NAME': os.environ.get('DB_NAME', 'CHPA_city'),
        'ENGINE': os.environ.get('DB_ENGINE', 'mssql'),
        'HOST': os.environ.get('DB_HOST', '(local)'),
        'PORT': os.environ.get('DB_PORT', ''),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'OPTIONS': {
            'driver': os.environ.get('DB_DRIVER', 'ODBC Driver 17 for SQL Server'),
        },
    }
}

# 缓存配置 - 使用环境变量指定的路径或容器内路径
CACHE_LOCATION = os.environ.get('CACHE_LOCATION', os.path.join(BASE_DIR, 'cache'))
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': CACHE_LOCATION,
    }
}

# 静态文件配置
STATIC_ROOT = os.environ.get('STATIC_ROOT', os.path.join(BASE_DIR, 'staticfiles'))
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

# 媒体文件配置
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(BASE_DIR, 'upload'))

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.environ.get('LOG_FILE', os.path.join(BASE_DIR, 'logs', 'django.log')),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': os.environ.get('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# 安全设置（生产环境）
if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False').lower() == 'true'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

