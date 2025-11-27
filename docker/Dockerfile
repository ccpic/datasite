# 使用官方 Python 3.8 镜像作为基础镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=datasite.settings_docker

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc-dev \
    unixodbc \
    freetds-dev \
    freetds-bin \
    tdsodbc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 配置 ODBC 驱动
RUN echo "[FreeTDS]\n\
Description=FreeTDS Driver\n\
Driver=/usr/lib/x86_64-linux-gnu/odbc/libtdsodbc.so\n\
Setup=/usr/lib/x86_64-linux-gnu/odbc/libtdsS.so" >> /etc/odbcinst.ini

# 复制依赖文件
COPY docker/requirements.txt /app/requirements.txt

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . /app/

# 复制 Docker 专用设置文件
COPY docker/settings_docker.py /app/datasite/settings_docker.py

# 创建必要的目录
RUN mkdir -p /app/cache /app/logs /app/staticfiles /app/upload

# 设置权限
RUN chmod +x /app/docker/entrypoint.sh

# 暴露端口
EXPOSE 8000

# 使用 entrypoint 脚本
ENTRYPOINT ["/app/docker/entrypoint.sh"]

