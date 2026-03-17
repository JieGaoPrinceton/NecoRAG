# Git 凭证配置指南

## ✅ 已配置成功

Git 远程仓库已配置为使用 OAuth2 + Token 格式：

```bash
origin  https://oauth2:95f0f0cea68ee3129be96762d8d50bf8@gitee.com/qijie2026/NecoRAG.git
```

## 🔑 Token 使用说明

### API Token vs Git Push Token

本项目使用的 Token：`95f0f0cea68ee3129be96762d8d50bf8`

**两种用途的格式：**

1. **API 调用** (Python requests 等)
   ```
   Authorization: token 95f0f0cea68ee3129be96762d8d50bf8
   ```

2. **Git 推送** (HTTPS)
   ```
   https://oauth2:95f0f0cea68ee3129be96762d8d50bf8@gitee.com/qijie2026/NecoRAG.git
   ```

⚠️ **重要：** Git HTTPS 必须使用 `oauth2:` 前缀！

## 📝 常用命令

### 推送到 Gitee

```bash
# 首次推送（设置上游分支）
git push -u origin main

# 后续推送
git push

# 强制推送（谨慎使用）
git push -f origin main
```

### 拉取代码

```bash
# 拉取并合并
git pull origin main

# 拉取并变基
git pull --rebase origin main
```

### 查看远程配置

```bash
# 查看远程仓库 URL
git remote -v

# 查看详细配置
git remote show origin
```

## 🔧 重新配置 Token

如果需要更换 Token，执行：

```bash
# 1. 清除当前配置
git remote set-url origin https://gitee.com/qijie2026/NecoRAG.git

# 2. 设置新 Token（替换 YOUR_TOKEN）
git remote set-url origin https://oauth2:YOUR_TOKEN@gitee.com/qijie2026/NecoRAG.git

# 3. 验证
git remote -v
```

## 🛡️ 安全建议

### ⚠️ 当前配置的风险

目前 Token 直接写在 Git 配置中，存在以下风险：

- ✅ `.git/config` 文件包含明文 Token
- ⚠️ 如果提交代码时不小心，可能泄露 Token
- ⚠️ 系统备份可能包含 Token

### ✅ 推荐的安全配置

#### 方法 1：使用 Git Credential Manager（最安全）

```bash
# macOS
brew install git-credential-manager

# 配置
git config --global credential.helper manager
git config --global credential.credentialStore gpg

# 下次 push 时会自动弹出登录窗口
```

#### 方法 2：使用 SSH 密钥（推荐）

```bash
# 1. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 添加公钥到 Gitee
# 访问：https://gitee.com/profile/ssh_keys

# 3. 切换为 SSH URL
git remote set-url origin git@gitee.com:qijie2026/NecoRAG.git

# 4. 测试
ssh -T git@gitee.com
```

#### 方法 3：临时输入密码（适合偶尔使用）

```bash
# 移除保存的凭证
git remote set-url origin https://gitee.com/qijie2026/NecoRAG.git

# 每次 push 时会提示输入
# 用户名：qijie2026
# 密码：95f0f0cea68ee3129be96762d8d50bf8
```

## 🐛 故障排除

### 问题 1: 403 Access denied

```bash
# 检查 Token 是否有效
curl -H "Authorization: token 95f0f0cea68ee3129be96762d8d50bf8" \
     https://gitee.com/api/v5/user

# 检查远程 URL
git remote -v

# 重新配置
git remote set-url origin https://oauth2:95f0f0cea68ee3129be96762d8d50bf8@gitee.com/qijie2026/NecoRAG.git
```

### 问题 2: 分支分歧

```bash
# 设置默认合并策略
git config pull.rebase false

# 或者使用 rebase
git pull --rebase origin main
```

### 问题 3: Token 过期

1. 访问 https://gitee.com/profile/personal_access_tokens
2. 创建新的 Personal Access Token
3. 确保勾选 `repo` 权限
4. 更新 Git 配置：
   ```bash
   git remote set-url origin https://oauth2:NEW_TOKEN@gitee.com/qijie2026/NecoRAG.git
   ```

## 📊 当前配置状态

```
✓ Git 远程仓库：已配置（OAuth2 格式）
✓ Token 权限：repo（完整仓库权限）
✓ 推送测试：成功
✓ 拉取测试：成功
```

## 🔗 相关链接

- [Gitee 个人访问令牌](https://gitee.com/profile/personal_access_tokens)
- [Gitee SSH 密钥配置](https://gitee.com/profile/ssh_keys)
- [Git 官方文档](https://git-scm.com/book/zh/v2)
