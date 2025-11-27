# Django 项目 Docker 部署指南

本指南说明如何在 Windows Server 2022 上使用 Docker 部署 Django 项目。

## 前置要求

1. Windows Server 2022
2. Docker Desktop for Windows 或 Docker Engine
3. Docker Compose（通常包含在 Docker Desktop 中）

## 快速开始

### 1. 配置环境变量

复制 `env.example` 为 `.env` 并修改配置：

```bash
cd docker
copy env.example .env
```

**注意**: 在 Windows 上，如果 `copy` 命令不可用，可以使用 PowerShell：
```powershell
Copy-Item env.example .env
```

编辑 `.env` 文件，至少修改以下关键配置：

- `SECRET_KEY`: 生成一个新的密钥（可以使用 `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`）
- `ALLOWED_HOSTS`: 设置你的域名或 IP 地址
- `DEBUG`: 生产环境设置为 `False`
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`: 数据库连接信息

### 2. 构建 Docker 镜像

```bash
docker compose build
```

### 3. 启动服务

如果使用外部 SQL Server 数据库：

```bash
# 编辑 docker-compose.yml，注释掉 mssql 服务或使用 profiles
docker compose up -d web
```

如果使用 docker-compose 中的 SQL Server 容器：

```bash
docker compose up -d
```

### 4. 查看日志

```bash
docker compose logs -f web
```

### 5. 访问应用

打开浏览器访问 `http://localhost:8000`

## 配置说明

### 数据库配置

#### 选项 1: 使用外部 SQL Server

1. 在 `.env` 文件中配置数据库连接信息：
```env
DB_HOST=your-sql-server-ip
DB_PORT=1433
DB_USER=your-username
DB_PASSWORD=your-password
DB_NAME=CHPA_city
```

2. 在 `docker-compose.yml` 中注释掉 `mssql` 服务或使用 `profiles: dontstart`

3. 确保 Windows Server 防火墙允许容器访问 SQL Server

#### 选项 2: 使用 Docker 容器中的 SQL Server

1. 在 `.env` 文件中配置：
```env
DB_HOST=mssql
DB_PORT=1433
DB_USER=sa
DB_PASSWORD=YourStrong@Passw0rd
```

2. 确保 `docker-compose.yml` 中的 `mssql` 服务未被禁用

### 静态文件配置

项目使用 `collectstatic` 收集静态文件到 `STATIC_ROOT`。如果需要挂载外部静态文件目录，可以在 `docker-compose.yml` 中配置 volumes。

### 缓存配置

默认使用文件缓存，缓存目录挂载为 Docker volume。如果需要使用 Redis 或 Memcached，需要：

1. 添加 Redis/Memcached 服务到 `docker-compose.yml`
2. 修改 `docker/settings_docker.py` 中的 `CACHES` 配置

## 常用命令

### 构建和启动

```bash
# 构建镜像
docker compose build

# 启动服务（后台运行）
docker compose up -d

# 启动服务（前台运行，查看日志）
docker compose up

# 停止服务
docker compose down

# 停止服务并删除 volumes
docker compose down -v
```

### 数据库操作

```bash
# 运行数据库迁移
docker compose exec web python manage.py migrate

# 创建超级用户
docker compose exec web python manage.py createsuperuser

# 进入 Django shell
docker compose exec web python manage.py shell
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs -f

# 查看 web 服务日志
docker compose logs -f web

# 查看最近 100 行日志
docker compose logs --tail=100 web
```

### 进入容器

```bash
# 进入 web 容器
docker compose exec web bash

# 进入 SQL Server 容器（如果使用）
docker compose exec mssql bash
```

## 故障排查

### 1. 数据库连接失败

**问题**: 容器无法连接到 SQL Server

**解决方案**:
- 检查 `.env` 文件中的数据库配置是否正确
- 确保 SQL Server 允许远程连接
- 检查 Windows 防火墙规则
- 如果使用外部数据库，确保容器网络可以访问数据库服务器

### 2. 静态文件 404 错误

**问题**: 静态文件无法加载

**解决方案**:
```bash
# 重新收集静态文件
docker compose exec web python manage.py collectstatic --noinput
```

### 3. 权限错误

**问题**: 容器内文件权限错误

**解决方案**:
```bash
# 修复权限
docker compose exec web chmod -R 755 /app/cache /app/logs /app/upload
```

### 4. 端口冲突

**问题**: 端口 8000 已被占用

**解决方案**:
- 修改 `docker-compose.yml` 中的端口映射，例如 `"8080:8000"`
- 或停止占用端口的其他服务

### 5. 内存不足

**问题**: 容器因内存不足而崩溃

**解决方案**:
- 减少 `GUNICORN_WORKERS` 数量
- 增加 Docker 的内存限制
- 优化查询，减少内存使用

## 生产环境建议

1. **使用反向代理**: 在 Docker 前使用 Nginx 或 IIS 作为反向代理
2. **启用 HTTPS**: 配置 SSL 证书，设置 `SECURE_SSL_REDIRECT=true`
3. **定期备份**: 设置数据库和媒体文件的定期备份
4. **监控日志**: 配置日志收集和监控系统
5. **资源限制**: 在 `docker-compose.yml` 中设置资源限制：
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
    reservations:
      cpus: '1'
      memory: 2G
```

## 安全注意事项

1. **不要**在 `.env` 文件中提交敏感信息到版本控制
2. **必须**在生产环境中设置强密码和密钥
3. **建议**定期更新依赖包以修复安全漏洞
4. **建议**使用 Docker secrets 或密钥管理服务存储敏感信息

## 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建镜像
docker compose build

# 重启服务
docker compose up -d

# 运行数据库迁移（如果有）
docker compose exec web python manage.py migrate
```

## 技术支持

如遇到问题，请检查：
1. Docker 日志: `docker compose logs`
2. Django 日志: `/app/logs/django.log`（容器内）
3. 代码审查文档: `docs/review.md`

