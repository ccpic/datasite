# Git 开发与部署版本控制指南

本文档说明如何使用 Git 管理开发版本和部署版本，实现代码的版本控制和环境切换。

## 分支策略

### 推荐的分支结构

```
master/main          # 生产环境分支（稳定版本）
├── develop          # 开发分支（日常开发）
├── staging          # 预发布分支（测试环境）
└── feature/*        # 功能分支（新功能开发）
```

### 分支说明

- **master/main**: 生产环境代码，只接受来自 staging 的合并，必须经过测试
- **develop**: 开发主分支，所有功能开发都基于此分支
- **staging**: 预发布分支，用于部署到测试环境
- **feature/***: 功能分支，开发新功能时创建

## 快速开始

### 1. 创建开发分支

```bash
# 从 master 创建 develop 分支
git checkout -b develop master

# 推送到远程
git push -u origin develop
```

### 2. 日常开发流程

```bash
# 切换到开发分支
git checkout develop

# 拉取最新代码
git pull origin develop

# 创建功能分支
git checkout -b feature/your-feature-name

# 开发完成后，提交代码
git add .
git commit -m "feat: 添加新功能"

# 推送到远程
git push origin feature/your-feature-name

# 合并到 develop（通过 Pull Request 或直接合并）
git checkout develop
git merge feature/your-feature-name
git push origin develop
```

### 3. 部署到测试环境

```bash
# 从 develop 创建或更新 staging 分支
git checkout -b staging develop
# 或如果已存在
git checkout staging
git merge develop

# 推送到远程
git push origin staging
```

### 4. 部署到生产环境

```bash
# 从 staging 合并到 master（确保代码已测试）
git checkout master
git merge staging

# 打标签（版本号）
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin master
git push origin v1.0.0
```

## 环境切换脚本

### Windows PowerShell 脚本

创建 `scripts/switch-env.ps1`:

```powershell
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment
)

$ErrorActionPreference = "Stop"

Write-Host "切换到 $Environment 环境..." -ForegroundColor Green

switch ($Environment) {
    "dev" {
        git checkout develop
        Write-Host "已切换到开发环境 (develop 分支)" -ForegroundColor Yellow
        Write-Host "使用开发配置: datasite.settings" -ForegroundColor Yellow
    }
    "staging" {
        git checkout staging
        Write-Host "已切换到测试环境 (staging 分支)" -ForegroundColor Yellow
        Write-Host "使用测试配置: datasite.settings_docker" -ForegroundColor Yellow
    }
    "prod" {
        git checkout master
        Write-Host "已切换到生产环境 (master 分支)" -ForegroundColor Red
        Write-Host "使用生产配置: datasite.settings_docker" -ForegroundColor Red
        Write-Host "警告: 这是生产环境，请谨慎操作！" -ForegroundColor Red
    }
}

Write-Host "`n当前分支: $(git branch --show-current)" -ForegroundColor Cyan
Write-Host "最新提交: $(git log -1 --oneline)" -ForegroundColor Cyan
```

### Bash 脚本（Linux/Mac/Git Bash）

创建 `scripts/switch-env.sh`:

```bash
#!/bin/bash

if [ -z "$1" ]; then
    echo "用法: ./switch-env.sh [dev|staging|prod]"
    exit 1
fi

ENV=$1

case $ENV in
    dev)
        git checkout develop
        echo "已切换到开发环境 (develop 分支)"
        echo "使用开发配置: datasite.settings"
        ;;
    staging)
        git checkout staging
        echo "已切换到测试环境 (staging 分支)"
        echo "使用测试配置: datasite.settings_docker"
        ;;
    prod)
        git checkout master
        echo "已切换到生产环境 (master 分支)"
        echo "使用生产配置: datasite.settings_docker"
        echo "警告: 这是生产环境，请谨慎操作！"
        ;;
    *)
        echo "错误: 无效的环境 '$ENV'"
        echo "用法: ./switch-env.sh [dev|staging|prod]"
        exit 1
        ;;
esac

echo ""
echo "当前分支: $(git branch --show-current)"
echo "最新提交: $(git log -1 --oneline)"
```

## Docker 环境切换

### 使用不同的 Docker Compose 文件

为不同环境创建不同的配置文件：

```bash
# 开发环境
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up

# 测试环境
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.staging.yml up

# 生产环境
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up
```

### 环境特定的配置文件

**docker/docker-compose.dev.yml**:
```yaml
version: '3.8'
services:
  web:
    environment:
      - DEBUG=True
      - DJANGO_SETTINGS_MODULE=datasite.settings
    volumes:
      - .:/app  # 挂载代码以便热重载
```

**docker/docker-compose.prod.yml**:
```yaml
version: '3.8'
services:
  web:
    environment:
      - DEBUG=False
      - DJANGO_SETTINGS_MODULE=datasite.settings_docker
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## 常用 Git 命令

### 查看当前状态

```bash
# 查看当前分支
git branch

# 查看所有分支（包括远程）
git branch -a

# 查看当前状态
git status

# 查看提交历史
git log --oneline --graph --all
```

### 切换分支

```bash
# 切换到指定分支
git checkout branch-name

# 创建并切换到新分支
git checkout -b new-branch-name

# 切换到上一个分支
git checkout -
```

### 合并分支

```bash
# 合并指定分支到当前分支
git merge branch-name

# 使用 rebase 合并（保持线性历史）
git rebase branch-name
```

### 处理冲突

```bash
# 查看冲突文件
git status

# 解决冲突后
git add .
git commit -m "解决合并冲突"
```

## 版本标签管理

### 创建标签

```bash
# 创建轻量标签
git tag v1.0.0

# 创建带注释的标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签到远程
git push origin v1.0.0

# 推送所有标签
git push origin --tags
```

### 查看和切换标签

```bash
# 查看所有标签
git tag

# 查看标签详情
git show v1.0.0

# 切换到标签（创建 detached HEAD）
git checkout v1.0.0

# 基于标签创建分支
git checkout -b release-v1.0.0 v1.0.0
```

## 最佳实践

### 1. 提交信息规范

使用约定式提交（Conventional Commits）：

```bash
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建/工具相关
```

示例：
```bash
git commit -m "feat: 添加用户认证功能"
git commit -m "fix: 修复 SQL 注入漏洞"
git commit -m "docs: 更新部署文档"
```

### 2. 分支保护规则

在 Git 托管平台（GitHub/GitLab）设置分支保护：

- **master**: 禁止直接推送，必须通过 Pull Request
- **staging**: 允许合并，但需要代码审查
- **develop**: 允许直接推送（开发分支）

### 3. 代码审查流程

```bash
# 1. 创建功能分支
git checkout -b feature/new-feature develop

# 2. 开发并提交
git add .
git commit -m "feat: 新功能"

# 3. 推送到远程
git push origin feature/new-feature

# 4. 创建 Pull Request (在 GitHub/GitLab 网页界面)

# 5. 代码审查通过后合并
```

### 4. 热修复（Hotfix）

生产环境紧急修复：

```bash
# 从 master 创建 hotfix 分支
git checkout -b hotfix/critical-bug master

# 修复并提交
git add .
git commit -m "fix: 修复关键 bug"

# 合并到 master 和 develop
git checkout master
git merge hotfix/critical-bug
git tag -a v1.0.1 -m "Hotfix: 修复关键 bug"

git checkout develop
git merge hotfix/critical-bug

# 推送
git push origin master
git push origin develop
git push origin v1.0.1
```

## 工作流示例

### 场景 1: 开发新功能

```bash
# 1. 确保 develop 是最新的
git checkout develop
git pull origin develop

# 2. 创建功能分支
git checkout -b feature/user-profile

# 3. 开发...
git add .
git commit -m "feat: 添加用户资料页面"

# 4. 推送到远程
git push origin feature/user-profile

# 5. 创建 Pull Request 合并到 develop
```

### 场景 2: 部署到生产

```bash
# 1. 确保 staging 已测试通过
git checkout staging
git pull origin staging

# 2. 合并到 master
git checkout master
git pull origin master
git merge staging

# 3. 打标签
git tag -a v1.1.0 -m "Release version 1.1.0"

# 4. 推送
git push origin master
git push origin v1.1.0

# 5. 部署（使用 Docker）
cd docker
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

### 场景 3: 回滚到上一个版本

```bash
# 1. 查看标签
git tag

# 2. 切换到上一个版本
git checkout v1.0.0

# 3. 创建临时分支
git checkout -b rollback-v1.0.0

# 4. 合并到 master（强制覆盖）
git checkout master
git reset --hard v1.0.0
git push origin master --force  # 谨慎使用！

# 5. 重新部署
cd docker
docker compose down
docker compose up -d --build
```

## 注意事项

1. **不要强制推送 master 分支**：除非是紧急回滚
2. **定期同步分支**：保持 develop 和 master 同步
3. **使用 Pull Request**：代码审查是质量保证的关键
4. **保护敏感信息**：确保 `.env` 文件在 `.gitignore` 中
5. **标签管理**：为每个生产部署打标签，便于追踪

## 故障排查

### 问题 1: 切换分支时提示有未提交的更改

```bash
# 方案 1: 提交更改
git add .
git commit -m "WIP: 临时提交"

# 方案 2: 暂存更改
git stash
git checkout other-branch
git stash pop  # 切换回来后恢复

# 方案 3: 放弃更改（谨慎！）
git checkout -- .
```

### 问题 2: 合并冲突

```bash
# 查看冲突文件
git status

# 手动解决冲突后
git add .
git commit -m "解决合并冲突"
```

### 问题 3: 误删分支

```bash
# 恢复本地分支
git checkout -b branch-name commit-hash

# 恢复远程分支（如果知道 commit hash）
git push origin commit-hash:refs/heads/branch-name
```

## 相关文档

- [Git 官方文档](https://git-scm.com/doc)
- [Git Flow 工作流](https://nvie.com/posts/a-successful-git-branching-model/)
- [约定式提交](https://www.conventionalcommits.org/)
- Docker 部署指南: `docker/README.md`

