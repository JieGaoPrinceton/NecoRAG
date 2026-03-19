---
name: version-management
description: 管理 NecoRAG 项目的版本号，支持手动递增、自动检测变更并智能更新版本、同步版本到所有 Markdown 文件和 pyproject.toml。Use when the user mentions version bump, version update, release new version, or when working with VERSION file and changelog updates.
---

# NecoRAG 版本管理技能

## 概述

NecoRAG 使用集中式版本管理策略，版本号存储在 `VERSION` 文件中，并通过工具同步到所有相关文件。

**版本号格式**: `MAJOR.MINOR.PATCH[-prerelease]`  
**示例**: `3.1.0-alpha`, `3.1.0-alpha`, `3.1.0-alpha`

## 核心文件

| 文件 | 用途 |
|------|------|
| `VERSION` | 主版本号文件 |
| `tools/version_manager.py` | 版本管理工具 |
| `tools/auto_version_control.py` | 自动版本控制系统 |
| `tools/auto_version_config.json` | 自动版本控制配置 |
| `pyproject.toml` | Python 包版本 |
| `CHANGELOG.md` | 更新日志 |

## 常用操作

### 1. 查看当前版本

```bash
python tools/version_manager.py show
```

### 2. 手动递增版本

```bash
# 递增补丁版本 (3.1.0-alpha -> 3.1.0-alpha)
python tools/version_manager.py bump patch

# 递增次要版本 (3.1.0-alpha -> 3.1.0-alpha)
python tools/version_manager.py bump minor

# 递增主版本 (3.1.0-alpha -> 3.1.0-alpha)
python tools/version_manager.py bump major
```

### 3. 直接设置版本

```bash
python tools/version_manager.py set 3.1.0-alpha
```

### 4. 同步版本到所有文件

```bash
# 实际同步
python tools/version_manager.py sync

# 预览模式（不实际写入）
python tools/version_manager.py sync --dry-run
```

### 5. 自动版本控制（推荐）

```bash
# 自动检测变更并更新版本
python tools/auto_version_control.py

# 交互模式（需要确认）
python tools/auto_version_control.py -i

# 预览模式
python tools/auto_version_control.py --dry-run

# 完全自动（无确认）
python tools/auto_version_control.py --auto
```

## 自动版本控制规则

自动版本控制系统根据变更类型智能决定版本递增级别：

| 变更类型 | 递增级别 | 触发条件 |
|---------|---------|---------|
| 🔴 重大重构 | major | 修改核心架构文件 (`src/necorag.py`, `src/core/`, `interface/`) |
| 🟢 新功能 | minor | 新增 Python 模块、新功能文件 |
| 🔵 Bug 修复 | patch | 修复代码、配置调整、文档更新 |
| 📝 文档更新 | patch | 修改 `.md` 文件 |
| ⚙️ 配置调整 | patch | 修改 `pyproject.toml`, `.env` 等 |
| 🧪 测试更新 | patch | 修改测试文件 |

## 版本同步范围

执行同步时，以下文件会被更新：

1. **pyproject.toml** - Python 包版本字段
2. **所有 Markdown 文件** - 版本号引用、徽章链接、最后更新日期

## 工作流程

### 发布新版本的标准流程

```
1. 完成功能开发或 Bug 修复
2. 运行自动版本控制：python tools/auto_version_control.py
3. 系统检测变更类型并建议版本递增
4. 确认更新（交互模式）或自动执行
5. 版本自动同步到所有文件
6. CHANGELOG.md 自动生成更新条目
7. 提交更改：git add . && git commit -m "chore: bump version to x.x.x"
```

### 手动版本管理流程

```
1. 递增版本：python tools/version_manager.py bump [level]
2. 或设置版本：python tools/version_manager.py set x.x.x
3. 同步到所有文件：python tools/version_manager.py sync
4. 提交更改
```

## 注意事项

- 版本号必须符合语义化版本规范：`MAJOR.MINOR.PATCH[-prerelease]`
- 同步操作会更新所有 Markdown 文件中的版本号引用
- 建议在版本更新后检查 `CHANGELOG.md` 确保条目正确
- 使用 `--dry-run` 预览变更，避免意外修改

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| VERSION 文件不存在 | 创建文件并写入初始版本，如 `3.1.0-alpha` |
| 版本号格式错误 | 检查格式是否为 `x.x.x` 或 `x.x.x-prerelease` |
| Git 状态获取失败 | 确保在项目根目录执行，且是 Git 仓库 |
| 同步未更新某些文件 | 检查文件编码是否为 UTF-8 |
