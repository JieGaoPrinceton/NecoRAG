# Gitee 推送工具使用指南

## 配置说明

本项目已配置使用 Gitee API 自动推送代码到 **gitee.com/qijie2026/NecoRAG**

### 配置文件

- **`.env`** - 存储 Gitee 认证信息
  ```bash
  GITEE_TOKEN=95f0f0cea68ee3129be96762d8d50bf8
  GITEE_OWNER=qijie2026
  GITEE_REPO=NecoRAG
  GITEE_API_BASE=https://gitee.com/api/v5
  ```

- **`.gitignore`** - 已添加 `.env` 防止敏感信息泄露

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

确保安装了以下新依赖：
- `requests>=2.0.1-alpha` - HTTP 请求库
- `python-dotenv>=2.0.1-alpha` - 环境变量管理

### 2. 推送项目到 Gitee

```bash
python tools/push_to_gitee.py
```

### 3. 功能特性

✅ **自动检测仓库** - 检查仓库是否存在，不存在则创建
✅ **智能文件上传** - 支持新增和更新文件
✅ **目录结构保持** - 自动处理多级目录
✅ **错误重试机制** - 网络问题自动重试 3 次
✅ **进度显示** - 实时显示上传进度和结果统计

### 4. 推送结果

成功推送后，访问：
**https://gitee.com/qijie2026/NecoRAG**

## 注意事项

⚠️ **Token 安全**
- 不要将 `.env` 文件提交到版本控制
- 定期更换 Gitee Token
- Token 权限：仓库管理（repo）

⚠️ **分支说明**
- 默认推送到 `main` 分支
- 如需推送到其他分支，修改 `tools/push_to_gitee.py` 中的 `branch` 参数

⚠️ **文件大小限制**
- Gitee API 对单个文件大小有限制（通常 < 10MB）
- 大文件建议使用 Git 命令行推送

## 故障排除

### 常见错误

1. **401 Unauthorized**
   - Token 无效或过期
   - 检查 `.env` 中的 Token 是否正确

2. **404 Not Found**
   - 仓库不存在或没有访问权限
   - 确认 `GITEE_OWNER` 和 `GITEE_REPO` 配置正确

3. **500 Internal Server Error**
   - Gitee API 临时故障
   - 脚本会自动重试，如持续失败请稍后再试

4. **content is empty**
   - 不能上传空文件
   - Gitee API 限制

## 手动验证

```bash
# 验证 Token 有效性
python -c "import requests; from dotenv import load_dotenv; import os; load_dotenv(); token=os.getenv('GITEE_TOKEN'); r=requests.get('https://gitee.com/api/v5/user', headers={'Authorization': f'token {token}'}); print(f'Status: {r.status_code}')"

# 检查仓库状态
python -c "import requests; from dotenv import load_dotenv; import os; load_dotenv(); token=os.getenv('GITEE_TOKEN'); r=requests.get('https://gitee.com/api/v5/repos/qijie2026/NecoRAG', headers={'Authorization': f'token {token}'}); print(f'Repo exists: {r.status_code == 200}')"
```

## 技术实现

推送工具使用 Gitee REST API v5：
- **创建仓库**: `POST /user/repos`
- **检查文件**: `GET /repos/{owner}/{repo}/contents/{path}`
- **创建文件**: `POST /repos/{owner}/{repo}/contents/{path}`
- **更新文件**: `PUT /repos/{owner}/{repo}/contents/{path}`

所有文件内容使用 Base64 编码后通过 API 传输。
