# Git 版本控制快速开始

## 最简单的使用方式

### 1. 创建开发分支（首次使用）

```bash
# 创建并切换到 develop 分支
git checkout -b develop master
git push -u origin develop
```

### 2. 日常开发

```bash
# 切换到开发分支
git checkout develop

# 拉取最新代码
git pull origin develop

# 开始开发...
# 提交代码
git add .
git commit -m "feat: 你的功能描述"
git push origin develop
```

### 3. 部署到生产

```bash
# 切换到生产分支
git checkout master

# 合并 develop 的代码（确保已测试）
git merge develop

# 打标签
git tag -a v1.0.0 -m "Release v1.0.0"

# 推送
git push origin master
git push origin v1.0.0
```

## 使用环境切换脚本

### Windows (PowerShell)

```powershell
# 切换到开发环境
.\scripts\switch-env.ps1 dev

# 切换到测试环境
.\scripts\switch-env.ps1 staging

# 切换到生产环境
.\scripts\switch-env.ps1 prod
```

### Linux/Mac/Git Bash

```bash
# 给脚本添加执行权限（首次使用）
chmod +x scripts/switch-env.sh

# 切换到开发环境
./scripts/switch-env.sh dev

# 切换到测试环境
./scripts/switch-env.sh staging

# 切换到生产环境
./scripts/switch-env.sh prod
```

## 常用命令速查

```bash
# 查看当前分支
git branch

# 查看所有分支
git branch -a

# 切换分支
git checkout branch-name

# 查看状态
git status

# 查看提交历史
git log --oneline --graph --all

# 创建标签
git tag -a v1.0.0 -m "版本说明"

# 查看标签
git tag
```

## 分支说明

- **master**: 生产环境，稳定版本
- **develop**: 开发环境，日常开发
- **staging**: 测试环境，预发布测试

## 注意事项

1. **不要直接修改 master 分支**：通过 develop → staging → master 的流程
2. **提交前检查**：确保代码可以正常运行
3. **使用有意义的提交信息**：如 `feat: 添加新功能`、`fix: 修复bug`
4. **定期同步**：经常 `git pull` 保持代码最新

## 更多信息

详细的工作流程和最佳实践，请查看 [Git 工作流完整指南](git-workflow.md)

