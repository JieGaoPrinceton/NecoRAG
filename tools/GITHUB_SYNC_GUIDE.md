# NecoRAG 双仓库同步指南

**版本**: v3.3.0-alpha  
**更新日期**: 2026-03-19

---

## 📋 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [配置步骤](#配置步骤)
- [使用工具](#使用工具)
- [常见问题](#常见问题)

---

## 🎯 概述

NecoRAG 项目采用**双仓库同步策略**,同时在 Gitee 和 GitHub 上托管代码:

- **Gitee (国内)**: https://gitee.com/qijie2026/NecoRAG
  - 优势：国内访问速度快
  - 适合：国内开发者和用户
  
- **GitHub (国际)**: https://github.com/JieGaoPrinceton/NecoRAG
  - 优势：国际影响力大，便于国际合作
  - 适合：国际开发者和用户

### 同步策略

```
本地开发 → 提交到 Git → 同步推送到 Gitee + GitHub
```

**优点**:
- ✅ 代码一致性：两个仓库保持完全同步
- ✅ 访问优化：国内外用户都能快速访问
- ✅ 灾备能力：一个仓库故障不影响另一个
- ✅ 影响力扩大：同时覆盖 Gitee 和 GitHub 社区

---

## 🚀 快速开始

### 方法一：使用 Python 工具（推荐）

```bash
cd tools
python sync_repos.py
```

### 方法二：使用 Shell 脚本

```bash
cd tools
./sync_to_github.sh
```

### 方法三：手动推送

```bash
# 推送到 Gitee
git push origin main

# 推送到 GitHub
git push github main
```

---

## ⚙️ 配置步骤

### 1. 检查远程仓库配置

```bash
git remote -v
```

**期望输出**:
```
origin  https://oauth2:xxx@gitee.com/qijie2026/NecoRAG.git (fetch)
origin  https://oauth2:xxx@gitee.com/qijie2026/NecoRAG.git (push)
github  https://github.com/JieGaoPrinceton/NecoRAG.git (fetch)
github  https://github.com/JieGaoPrinceton/NecoRAG.git (push)
```

### 2. 如果缺少 GitHub 远程仓库

```bash
# 添加 GitHub 远程仓库
git remote add github https://github.com/JieGaoPrinceton/NecoRAG.git

# 验证配置
git remote -v
```

### 3. 配置 GitHub Token（可选但推荐）

为了避免每次推送都输入密码，建议配置 Personal Access Token:

#### 步骤 1: 创建 Token

1. 访问 GitHub Settings → Developer settings → Personal access tokens
2. 点击 "Generate new token"
3. 选择权限：`repo` (Full control of private repositories)
4. 生成并复制 Token

#### 步骤 2: 使用 Token

**方法 A: 在 URL 中包含 Token**
```bash
git remote set-url github https://YOUR_TOKEN@github.com/JieGaoPrinceton/NecoRAG.git
```

**方法 B: 使用 Git Credential Manager（推荐）**
```bash
# Windows/Mac: 自动弹出登录窗口
git push github main

# Linux: 配置凭证存储
git config --global credential.helper store
git push github main  # 输入一次后记住
```

---

## 🛠️ 使用工具

### 1. Python 同步工具 (`sync_repos.py`)

**功能特性**:
- ✅ 交互式菜单
- ✅ 彩色输出
- ✅ 状态检查
- ✅ 错误处理
- ✅ 详细提示

**使用方法**:
```bash
cd tools
python sync_repos.py
```

**输出示例**:
```
╔════════════════════════════════════════════════════╗
║   NecoRAG 双仓库同步工具                           ║
╚════════════════════════════════════════════════════╝

📍 当前分支：main
⚠️  有以下未提交的更改:
  M tools/sync_repos.py

请选择同步方式:
  1) 仅推送到 Gitee (origin)
  2) 仅推送到 GitHub (github)
  3) 同时推送到两个仓库 (推荐)
  4) 只查看状态，不推送

请输入选项 (1/2/3/4): 3

🚀 开始同步到两个仓库...
──────────────────────────────────────────────────

🚀 推送到 origin...
──────────────────────────────────────────────────
✅ origin 推送成功!

🚀 推送到 github...
──────────────────────────────────────────────────
✅ github 推送成功!

╔════════════════════════════════════════════════════╗
║   ✅ 同步完成！两个仓库都已更新                    ║
╚════════════════════════════════════════════════════╝

📍 Gitee 仓库：https://gitee.com/qijie2026/NecoRAG
📍 GitHub 仓库：https://github.com/JieGaoPrinceton/NecoRAG

✅ 操作完成！
```

### 2. Shell 同步脚本 (`sync_to_github.sh`)

**功能特性**:
- ✅ Bash 脚本，跨平台
- ✅ 彩色输出
- ✅ 交互式选择
- ✅ 详细日志

**使用方法**:
```bash
cd tools
./sync_to_github.sh
```

### 3. Git 配置别名（可选）

为了方便使用，可以配置 Git 别名:

```bash
# 配置同步别名
git config --global alias.sync-gitee '!git push origin $(git branch --show-current)'
git config --global alias.sync-github '!git push github $(git branch --show-current)'
git config --global alias.sync-all '!git push origin $(git branch --show-current) && git push github $(git branch --show-current)'

# 使用
git sync-all  # 一键同步到两个仓库
```

---

## 🔄 完整工作流

### 日常开发流程

```bash
# 1. 本地开发和提交
git add .
git commit -m "feat: add new feature"

# 2. 同步到两个仓库
cd tools
python sync_repos.py
# 选择选项 3 (同时推送)

# 或使用别名
git sync-all
```

### 版本发布流程

```bash
# 1. 创建版本标签
git tag -a v3.3.0-alpha -m "Release version 3.3.0-alpha"

# 2. 推送标签到两个仓库
git push origin v3.3.0-alpha
git push github v3.3.0-alpha

# 或使用工具
python sync_repos.py
```

### 分支管理

```bash
# 创建新分支
git checkout -b feature/new-feature

# 推送到两个仓库
git push -u origin feature/new-feature
git push -u github feature/new-feature

# 后续只需
git push  # 自动推送到 origin
git push github  # 手动推送到 github
```

---

## ❓ 常见问题

### Q1: GitHub 推送失败，提示认证错误

**解决方案**:

```bash
# 方法 1: 使用 Personal Access Token
git remote set-url github https://YOUR_TOKEN@github.com/JieGaoPrinceton/NecoRAG.git
git push github main

# 方法 2: 清除缓存重新认证
git credential-cache exit
git push github main  # 会重新提示输入

# 方法 3: 使用 SSH 密钥
git remote set-url github git@github.com:JieGaoPrinceton/NecoRAG.git
```

### Q2: 两个仓库内容不一致怎么办？

**检查方法**:
```bash
# 查看两个仓库的提交历史
git log origin/main --oneline -5
git log github/main --oneline -5

# 如果有差异，强制同步
git fetch origin
git reset --hard origin/main
git push github main --force
```

### Q3: 只想同步特定分支？

```bash
# 只同步 main 分支
git push origin main
git push github main

# 只同步 develop 分支
git push origin develop
git push github develop

# 不同步某个分支
# 不要在该分支设置 upstream 即可
```

### Q4: 网络慢怎么办？

**Gitee 方案**:
```bash
# 国内用户优先使用 Gitee
git push origin main
```

**GitHub 加速**:
```bash
# 使用镜像（如果可用）
git remote set-url github https://ghproxy.com/https://github.com/JieGaoPrinceton/NecoRAG.git
```

### Q5: 如何取消 GitHub 远程仓库？

```bash
# 移除 GitHub 远程仓库
git remote remove github

# 验证
git remote -v
# 应该只显示 origin (Gitee)
```

---

## 📊 仓库对比

| 特性 | Gitee | GitHub |
|-----|-------|--------|
| **访问速度** | 国内快 | 国际快 |
| **用户群体** | 中国开发者 | 全球开发者 |
| **功能** | 基础 Git 功能 | 完整的 CI/CD、Actions |
| **集成** | 国内服务集成 | 国际服务集成 |
| **语言** | 中文界面 | 英文界面 |
| **推荐用途** | 国内分发、备份 | 国际推广、合作 |

---

## 🎓 最佳实践

### 1. 提交规范

遵循 Conventional Commits 规范:
```bash
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"
git commit -m "docs: update README"
git commit -m "refactor: improve code structure"
```

### 2. 分支策略

```
main (生产环境)
  ├─ develop (开发分支)
  │   ├─ feature/user-auth (功能分支)
  │   └─ feature/search (功能分支)
  └─ hotfix/critical-bug (热修复)
```

### 3. 标签管理

```bash
# 语义化版本
v3.3.0-alpha    # 预发布版本
v3.3.0-alpha          # 正式版本
v3.3.0-alpha          # Bug 修复版本
v3.3.0-alpha     # 大版本测试版
```

### 4. 同步频率

- ✅ **每次提交后**: 立即同步到两个仓库
- ✅ **每日结束**: 确保当天工作已同步
- ✅ **版本发布前**: 必须确认两个仓库一致

---

## 🔧 自动化脚本

### GitHub Actions 自动同步

如果需要自动化同步，可以在 GitHub 上配置 Actions:

```yaml
# .github/workflows/sync.yml
name: Sync to Gitee

on:
  push:
    branches: [main]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Add Gitee remote
        run: |
          git remote add gitee https://gitee.com/qijie2026/NecoRAG.git
      
      - name: Push to Gitee
        run: |
          git push gitee main --force
        env:
          GITEE_TOKEN: ${{ secrets.GITEE_TOKEN }}
```

---

## 📚 相关资源

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub 文档](https://docs.github.com/)
- [Gitee 文档](https://gitee.com/help)
- [Personal Access Token 配置](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

---

## 🎉 总结

通过双仓库同步策略，NecoRAG 项目实现了:

✅ **高可用性**: 两个仓库互为备份  
✅ **访问优化**: 国内外用户都能快速访问  
✅ **影响力扩大**: 同时覆盖 Gitee 和 GitHub 社区  
✅ **开发便利**: 简单的工具实现一键同步  

**推荐工作流程**:
```bash
# 开发 → 提交 → 同步
git add .
git commit -m "feat: your feature"
cd tools
python sync_repos.py  # 选择选项 3
```

---

<div align="center">

**Let's make AI think like a brain!** 🧠

[NecoRAG Team](https://github.com/JieGaoPrinceton/NecoRAG)

</div>
