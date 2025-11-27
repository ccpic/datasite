#!/bin/bash
set -e

echo "Starting Django application..."

# 等待数据库连接（如果需要）
if [ -n "$DB_HOST" ] && [ "$DB_HOST" != "(local)" ]; then
    echo "Waiting for database connection..."
    until python -c "import pymssql; pymssql.connect(server='$DB_HOST', user='$DB_USER', password='$DB_PASSWORD', database='$DB_NAME')" 2>/dev/null; do
        echo "Database is unavailable - sleeping"
        sleep 1
    done
    echo "Database is up - continuing"
fi

# 运行数据库迁移
echo "Running database migrations..."
python manage.py migrate --noinput

# 收集静态文件
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# 创建必要的目录
mkdir -p /app/cache
mkdir -p /app/logs
mkdir -p /app/staticfiles
mkdir -p /app/upload

# 可选：运行 Django 部署检查
if [ "$RUN_DEPLOY_CHECK" = "true" ]; then
    echo "Running deployment checks..."
    python manage.py check --deploy
fi

# 启动 Gunicorn
echo "Starting Gunicorn..."
exec gunicorn datasite.wsgi:application \
    --config docker/gunicorn.conf.py \
    --bind 0.0.0.0:8000 \
    --access-logfile - \
    --error-logfile -

