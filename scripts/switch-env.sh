#!/bin/bash
# Git 环境切换脚本 (Bash)
# 用法: ./scripts/switch-env.sh [dev|staging|prod]

set -e

if [ -z "$1" ]; then
    echo "用法: ./switch-env.sh [dev|staging|prod]"
    exit 1
fi

ENV=$1

echo "========================================"
echo "Git 环境切换工具"
echo "========================================"
echo ""

# 检查是否有未提交的更改
if [ -n "$(git status --porcelain)" ]; then
    echo "警告: 检测到未提交的更改:"
    git status --short
    echo ""
    read -p "是否继续? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "操作已取消"
        exit 1
    fi
fi

echo "切换到 $ENV 环境..."
echo ""

case $ENV in
    dev)
        # 检查 develop 分支是否存在
        if ! git show-ref --verify --quiet refs/heads/develop && ! git show-ref --verify --quiet refs/remotes/origin/develop; then
            echo "创建 develop 分支..."
            git checkout -b develop master
        else
            git checkout develop
            git pull origin develop 2>/dev/null || true
        fi
        echo "✓ 已切换到开发环境 (develop 分支)"
        echo "  使用配置: datasite.settings"
        echo "  建议: 使用本地数据库进行开发"
        ;;
    staging)
        # 检查 staging 分支是否存在
        if ! git show-ref --verify --quiet refs/heads/staging && ! git show-ref --verify --quiet refs/remotes/origin/staging; then
            echo "创建 staging 分支..."
            if git show-ref --verify --quiet refs/heads/develop; then
                git checkout -b staging develop 2>/dev/null || git checkout -b staging master
            else
                git checkout -b staging master
            fi
        else
            git checkout staging
            git pull origin staging 2>/dev/null || true
        fi
        echo "✓ 已切换到测试环境 (staging 分支)"
        echo "  使用配置: datasite.settings_docker"
        echo "  建议: 使用 Docker 部署到测试服务器"
        ;;
    prod)
        git checkout master
        git pull origin master 2>/dev/null || true
        echo "✓ 已切换到生产环境 (master 分支)"
        echo "  使用配置: datasite.settings_docker"
        echo ""
        echo "⚠️  警告: 这是生产环境，请谨慎操作！"
        echo "  建议操作:"
        echo "    1. 检查当前代码版本"
        echo "    2. 确认环境变量配置正确"
        echo "    3. 运行测试后再部署"
        ;;
    *)
        echo "错误: 无效的环境 '$ENV'"
        echo "用法: ./switch-env.sh [dev|staging|prod]"
        exit 1
        ;;
esac

echo ""
echo "当前状态:"
echo "  分支: $(git branch --show-current)"
echo "  最新提交: $(git log -1 --oneline)"
echo "  远程状态: $(git status -sb | grep -o '\[.*\]' || echo '无')"

echo ""
echo "下一步操作建议:"
case $ENV in
    dev)
        echo "  - 运行: python manage.py runserver"
        echo "  - 或使用: docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up"
        ;;
    staging)
        echo "  - 检查: docker/docker-compose.yml 配置"
        echo "  - 运行: docker compose build && docker compose up -d"
        ;;
    prod)
        echo "  - 检查: docker/.env 文件配置"
        echo "  - 构建: docker compose build"
        echo "  - 部署: docker compose up -d"
        ;;
esac

echo ""

