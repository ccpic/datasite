# Docker 部署文件总结

本文档列出了为 Django 项目 Docker 化创建的所有文件及其用途。

## 文件清单

### 1. `docker/requirements.txt`
- **用途**: Docker 环境专用的 Python 依赖列表
- **说明**: 移除了 Windows 特定的 wheel 文件引用，添加了生产环境必需的包（如 gunicorn、whitenoise）
- **关键依赖**: Django 3.0.8, pymssql, SQLAlchemy, pandas, gunicorn

### 2. `docker/settings_docker.py`
- **用途**: Docker 环境专用的 Django 设置文件
- **说明**: 通过环境变量覆盖原始 settings.py 中的配置，无需修改业务代码
- **主要功能**:
  - 从环境变量读取 SECRET_KEY, DEBUG, ALLOWED_HOSTS
  - 配置数据库连接（支持外部 SQL Server）
  - 配置缓存、静态文件、媒体文件路径
  - 添加日志配置
  - 生产环境安全设置

### 3. `docker/entrypoint.sh`
- **用途**: 容器启动脚本
- **说明**: 执行容器启动时的初始化任务
- **执行步骤**:
  1. 等待数据库连接就绪
  2. 运行数据库迁移
  3. 收集静态文件
  4. 创建必要目录
  5. 可选：运行部署检查
  6. 启动 Gunicorn 服务器

### 4. `docker/gunicorn.conf.py`
- **用途**: Gunicorn WSGI 服务器配置文件
- **说明**: 配置工作进程数、超时时间、日志等
- **可配置项**: 通过环境变量调整 workers、timeout、log level 等

### 5. `docker/Dockerfile`
- **用途**: Docker 镜像构建文件
- **说明**: 定义如何构建应用容器镜像
- **主要步骤**:
  1. 基于 Python 3.8-slim 镜像
  2. 安装系统依赖（ODBC 驱动、FreeTDS 等）
  3. 安装 Python 依赖
  4. 复制项目文件
  5. 设置权限和启动脚本

### 6. `docker/docker-compose.yml`
- **用途**: Docker Compose 配置文件
- **说明**: 定义多容器应用的编排
- **服务**:
  - `web`: Django 应用容器
  - `mssql`: 可选的 SQL Server 容器（可通过 profiles 禁用）
- **功能**: 配置网络、卷、环境变量、端口映射等

### 7. `docker/env.example`
- **用途**: 环境变量配置示例文件
- **说明**: 包含所有可配置的环境变量及其说明
- **使用方法**: 复制为 `.env` 并修改实际值

### 8. `docker/README.md`
- **用途**: Docker 部署完整指南
- **内容**: 
  - 快速开始指南
  - 配置说明
  - 常用命令
  - 故障排查
  - 生产环境建议

### 9. `docs/review.md`
- **用途**: 代码审查报告
- **内容**: 
  - 安全漏洞分析（SQL 注入、硬编码密钥等）
  - 性能问题识别
  - 代码质量评估
  - Docker 化需要的代码改动建议

## 使用流程

### 首次部署

1. **准备环境变量**
   ```bash
   cd docker
   copy env.example .env
   # 编辑 .env 文件，配置数据库连接等信息
   ```

2. **构建镜像**
   ```bash
   docker compose build
   ```

3. **启动服务**
   ```bash
   # 如果使用外部数据库，先禁用 mssql 服务
   docker compose up -d web
   ```

4. **检查日志**
   ```bash
   docker compose logs -f web
   ```

### 日常维护

- **查看日志**: `docker compose logs -f web`
- **重启服务**: `docker compose restart web`
- **更新代码**: 重新构建镜像并重启
- **数据库迁移**: `docker compose exec web python manage.py migrate`

## 重要注意事项

1. **不修改业务代码**: 所有 Docker 相关配置都在 `docker/` 目录下，不会影响现有业务代码

2. **环境变量**: 必须正确配置 `.env` 文件，特别是：
   - SECRET_KEY（生产环境必须更改）
   - 数据库连接信息
   - ALLOWED_HOSTS

3. **数据库连接**: 
   - 如果使用外部 SQL Server，确保网络可达
   - 如果使用容器内 SQL Server，注意数据持久化

4. **静态文件**: 首次部署需要运行 `collectstatic`（entrypoint.sh 已自动执行）

5. **安全**: 
   - 生产环境必须设置 `DEBUG=False`
   - 使用强密码和密钥
   - 不要将 `.env` 文件提交到版本控制

## 后续建议

根据 `docs/review.md` 中的审查结果，建议：

1. **立即修复**: SQL 注入漏洞（禁用或限制 customized_sql 功能）
2. **代码重构**: 统一 sqlparse() 函数到 commons.py
3. **性能优化**: 添加查询结果数量限制，优化大数据集处理
4. **安全加固**: 使用参数化查询替代字符串拼接

## 技术支持

- 查看 `docker/README.md` 获取详细部署指南
- 查看 `docs/review.md` 了解代码审查结果
- 检查容器日志排查问题

