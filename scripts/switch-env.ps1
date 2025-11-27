# Git 环境切换脚本 (PowerShell)
# 用法: .\scripts\switch-env.ps1 [dev|staging|prod]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Git 环境切换工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否有未提交的更改
$status = git status --porcelain
if ($status) {
    Write-Host "警告: 检测到未提交的更改:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    $response = Read-Host "是否继续? (y/N)"
    if ($response -ne "y" -and $response -ne "Y") {
        Write-Host "操作已取消" -ForegroundColor Red
        exit 1
    }
}

Write-Host "切换到 $Environment 环境..." -ForegroundColor Green
Write-Host ""

switch ($Environment) {
    "dev" {
        # 检查 develop 分支是否存在
        $branchExists = git branch -a | Select-String -Pattern "develop" -Quiet
        if (-not $branchExists) {
            Write-Host "创建 develop 分支..." -ForegroundColor Yellow
            git checkout -b develop master
        } else {
            git checkout develop
            git pull origin develop 2>$null
        }
        Write-Host "✓ 已切换到开发环境 (develop 分支)" -ForegroundColor Green
        Write-Host "  使用配置: datasite.settings" -ForegroundColor Gray
        Write-Host "  建议: 使用本地数据库进行开发" -ForegroundColor Gray
    }
    "staging" {
        # 检查 staging 分支是否存在
        $branchExists = git branch -a | Select-String -Pattern "staging" -Quiet
        if (-not $branchExists) {
            Write-Host "创建 staging 分支..." -ForegroundColor Yellow
            git checkout -b staging develop 2>$null
            if ($LASTEXITCODE -ne 0) {
                git checkout -b staging master
            }
        } else {
            git checkout staging
            git pull origin staging 2>$null
        }
        Write-Host "✓ 已切换到测试环境 (staging 分支)" -ForegroundColor Yellow
        Write-Host "  使用配置: datasite.settings_docker" -ForegroundColor Gray
        Write-Host "  建议: 使用 Docker 部署到测试服务器" -ForegroundColor Gray
    }
    "prod" {
        git checkout master
        git pull origin master 2>$null
        Write-Host "✓ 已切换到生产环境 (master 分支)" -ForegroundColor Red
        Write-Host "  使用配置: datasite.settings_docker" -ForegroundColor Gray
        Write-Host ""
        Write-Host "⚠️  警告: 这是生产环境，请谨慎操作！" -ForegroundColor Red
        Write-Host "  建议操作:" -ForegroundColor Yellow
        Write-Host "    1. 检查当前代码版本" -ForegroundColor Yellow
        Write-Host "    2. 确认环境变量配置正确" -ForegroundColor Yellow
        Write-Host "    3. 运行测试后再部署" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "当前状态:" -ForegroundColor Cyan
Write-Host "  分支: $(git branch --show-current)" -ForegroundColor White
Write-Host "  最新提交: $(git log -1 --oneline --no-color)" -ForegroundColor White
Write-Host "  远程状态: $(git status -sb --porcelain | Select-String -Pattern '\[.*\]')" -ForegroundColor White

Write-Host ""
Write-Host "下一步操作建议:" -ForegroundColor Cyan
switch ($Environment) {
    "dev" {
        Write-Host "  - 运行: python manage.py runserver" -ForegroundColor Gray
        Write-Host "  - 或使用: docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up" -ForegroundColor Gray
    }
    "staging" {
        Write-Host "  - 检查: docker/docker-compose.yml 配置" -ForegroundColor Gray
        Write-Host "  - 运行: docker compose build && docker compose up -d" -ForegroundColor Gray
    }
    "prod" {
        Write-Host "  - 检查: docker/.env 文件配置" -ForegroundColor Gray
        Write-Host "  - 构建: docker compose build" -ForegroundColor Gray
        Write-Host "  - 部署: docker compose up -d" -ForegroundColor Gray
    }
}

Write-Host ""

