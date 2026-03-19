# NecoRAG 版本管理指南

## 📋 概述

NecoRAG 使用集中式的版本号管理系统，确保整个项目中所有文件的版本号保持一致。

## 📁 文件结构

```
NecoRAG/
├── VERSION                      # 版本号文件（唯一数据源）
├── pyproject.toml              # Python 项目配置（包含版本号）
├── tools/
│   └── version_manager.py      # 版本管理工具
└── *.md                        # 所有 Markdown 文档
```

## 🎯 版本号格式

采用语义化版本号（Semantic Versioning）格式：

```
主版本号。次版本号.补丁号 - 预发布标识
例如：3.0.1-alpha, 3.0.1-alpha, 3.0.1-alpha
```

- **主版本号 (Major)**: 重大更新，不兼容的 API 变更
- **次版本号 (Minor)**: 新功能，向后兼容
- **补丁号 (Patch)**: Bug 修复，向后兼容
- **预发布标识**: `-alpha`, `-beta`, `-rc` 等

## 🚀 快速开始

### 查看当前版本

```bash
cd /Users/ll/NecoRAG
python tools/version_manager.py show
```

输出示例：
```
============================================================
NecoRAG 版本信息
============================================================
当前版本：3.0.1-alpha

版本组成:
  主版本号 (Major): 1
  次版本号 (Minor): 9
  补丁号 (Patch):   0
  预发布标识：      -alpha

项目统计:
  Markdown 文件数：45
  VERSION 文件：   /Users/ll/NecoRAG/VERSION
  pyproject 文件： /Users/ll/NecoRAG/pyproject.toml
============================================================
```

### 递增版本号

#### 递增补丁号（推荐用于小更新）

```bash
python tools/version_manager.py bump patch
# 3.0.1-alpha -> 3.0.1-alpha
```

#### 递增次版本号（添加新功能）

```bash
python tools/version_manager.py bump minor
# 3.0.1-alpha -> 3.0.1-alpha
```

#### 递增主版本号（重大变更）

```bash
python tools/version_manager.py bump major
# 3.0.1-alpha -> 3.0.1-alpha
```

### 直接设置版本号

```bash
python tools/version_manager.py set 3.0.1-alpha
```

### 同步版本号到所有文件

```bash
# 实际执行同步
python tools/version_manager.py sync

# 预览模式（查看将要进行的更改）
python tools/version_manager.py sync --dry-run
```

## 📝 自动更新的文件

版本管理工具会自动更新以下位置的版本号：

### 1. 核心配置文件
- `VERSION` - 版本号源文件
- `pyproject.toml` - Python 项目版本

### 2. Markdown 文档中的版本引用

工具会智能识别并更新以下模式：

| 模式 | 示例 | 替换为 |
|------|------|--------|
| `v3.0.1-alpha` | README 徽章 | `v3.0.1-alpha` |
| `V3.0.1-alpha-alpha-alpha-alpha-alpha-alpha` | 标题中的大写版本 | `V3.0.1-alpha-alpha-alpha-alpha-alpha-alpha` |
| `3.0.1-alpha` | 纯文本版本号 | `3.0.1-alpha` |
| `v3.0` | 短版本号 | `v3.0` |
| `**最后更新**: 2026-03-19` | 更新日期 | `**最后更新**: 2026-03-19` |

### 3. 更新的文档类型

- ✅ README.md - 项目主文档
- ✅ QUICKSTART.md - 快速开始指南
- ✅ CHANGELOG.md - 更新日志
- ✅ 所有模块的 README.md
- ✅ Wiki 文档
- ✅ 设计文档
- ✅ 所有其他 `.md` 文件

## 🔄 标准工作流程

### 发布新版本的标准流程

```bash
# 1. 确认当前版本
python tools/version_manager.py show

# 2. 递增版本号（根据更新类型选择）
python tools/version_manager.py bump minor  # 或 major/patch

# 3. 验证更新（可选）
python tools/version_manager.py sync --dry-run

# 4. 提交更改
git add VERSION pyproject.toml *.md
git commit -m "chore: bump version to 3.0.1-alpha"

# 5. 打标签（可选）
git tag v3.0.1-alpha
git push origin v3.0.1-alpha
```

### 紧急修复流程

```bash
# 1. 递增补丁号
python tools/version_manager.py bump patch

# 2. 自动同步到所有文件
python tools/version_manager.py sync

# 3. 提交并推送
git add .
git commit -m "fix: release 3.0.1-alpha with critical bug fixes"
git push
```

## 💡 最佳实践

### ✅ 推荐做法

1. **每次发布都更新版本**
   - 无论更新大小，都应该递增版本号
   - 保持版本号的准确性和可信度

2. **遵循语义化版本规范**
   - Bug 修复 → `bump patch`
   - 新功能 → `bump minor`
   - 破坏性变更 → `bump major`

3. **在提交前同步版本**
   - 确保所有文档的版本号一致
   - 避免版本混乱

4. **使用预发布标识**
   - 开发中版本：`-alpha`
   - 测试版本：`-beta`
   - 候选版本：`-rc`

### ❌ 避免的做法

1. **不要手动修改 VERSION 文件**
   - 始终使用版本管理工具
   - 避免格式错误

2. **不要跳过同步步骤**
   - 确保所有文件的版本一致
   - 避免文档与代码版本不匹配

3. **不要随意跳号**
   - 保持版本号的连续性
   - 便于追踪和回滚

## 🔧 高级用法

### 批量检查版本一致性

```bash
# 检查所有文件中的版本号是否一致
grep -r "v1\\.9\\.0" --include="*.md" .
```

### 自定义排除目录

编辑 `tools/version_manager.py`，修改 `exclude_dirs` 集合：

```python
exclude_dirs = {
    '.git', '__pycache__', 'node_modules', 
    '.pytest_cache', '.mypy_cache', 'venv', 
    'env', '.venv', 'dist', 'build',
    'your_custom_dir'  # 添加你的自定义目录
}
```

### 集成到 CI/CD

在 GitHub Actions 或其他 CI 工具中使用：

```yaml
- name: Bump version
  run: python tools/version_manager.py bump patch

- name: Commit version change
  run: |
    git config --local user.email "action@github.com"
    git config --local user.name "GitHub Action"
    git add VERSION pyproject.toml
    git commit -m "chore: bump version" || echo "No changes to commit"
```

## 📊 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 3.0.1-alpha | 2026-03-19 | 智能路由与策略融合引擎 ⭐ |
| 3.0.1-alpha | 2026-03-19 | Interface 模块增强 |
| 3.0.1-alpha | 2026-03-19 | 可视化调试面板 ⭐ |
| 3.0.1-alpha | 2026-03-17 | MVP 版本发布 |

## 🆘 故障排查

### 问题 1: 版本号格式错误

**错误信息**: `无效的版本号格式`

**解决方案**:
```bash
# 使用正确的格式
python tools/version_manager.py set 3.0.1-alpha
# 或
python tools/version_manager.py set 3.0.1-alpha
```

### 问题 2: 某些文件未更新

**可能原因**: 文件位于排除目录中

**解决方案**:
1. 检查文件是否在 `exclude_dirs` 中
2. 手动运行 `grep` 检查版本号
3. 如有必要，手动更新该文件

### 问题 3: 同步失败

**解决方案**:
```bash
# 使用预览模式查看详细错误
python tools/version_manager.py sync --dry-run

# 检查文件权限
ls -la VERSION pyproject.toml

# 以管理员权限运行（如果需要）
sudo python tools/version_manager.py sync
```

## 📚 相关资源

- [语义化版本规范 3.0.1-alpha](https://semver.org/lang/zh-CN/)
- [Keep a Changelog](https://keepachangelog.com/zh-CN/3.0.1-alpha/)
- [Python 打包版本规范](https://packaging.python.org/en/latest/specifications/version-specifiers/)

---

<div align="center">

**NecoRAG 版本管理工具**  
让版本管理变得简单、准确、自动化！ 🚀

</div>
