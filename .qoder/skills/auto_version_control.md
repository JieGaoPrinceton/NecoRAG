# NecoRAG 自动版本控制技能

## 📋 技能说明

**名称**: auto-version-control  
**功能**: 自动检测项目变更并递增版本号，同步到所有文件  
**触发时机**: 每次项目代码提交或配置变更时

---

## 🎯 核心能力

1. **智能检测变更** - 识别代码、文档、配置等不同类型的修改
2. **自动递增版本号** - 根据变更类型选择递增级别（major/minor/patch）
3. **批量同步版本** - 更新项目中所有文件的版本号引用
4. **生成更新日志** - 自动记录本次版本变更的详细信息

---

## 🔧 使用方法

### 方式 1：手动触发

```bash
cd /Users/ll/NecoRAG
python tools/auto_version_control.py
```

### 方式 2：Git Hook 自动触发

在 `.git/hooks/pre-commit` 中添加：

```bash
#!/bin/bash
# 自动版本控制
python tools/auto_version_control.py --auto
```

### 方式 3：CI/CD 集成

在 GitHub Actions 或 GitLab CI 配置中调用此脚本。

---

## 📊 变更类型与版本递增规则

| 变更类型 | 检测条件 | 递增级别 | 示例 |
|---------|---------|---------|------|
| **重大重构** | 修改核心架构文件 | major | 3.0.0-alpha → 3.0.0-alpha |
| **新功能** | 新增模块/功能文件 | minor | 3.0.0-alpha → 3.0.0-alpha |
| **Bug 修复** | 修复错误、优化性能 | patch | 3.0.0-alpha → 3.0.0-alpha |
| **文档更新** | 仅修改 .md 文件 | patch | 3.0.0-alpha → 3.0.0-alpha |
| **配置调整** | 修改配置文件 | patch | 3.0.0-alpha → 3.0.0-alpha |

---

## 💡 使用示例

### 示例 1：自动检测并更新

```bash
$ python tools/auto_version_control.py

============================================================
NecoRAG 自动版本控制系统
============================================================

检测到以下变更:
  📝 文档更新：README.md, QUICKSTART.md
  🔧 配置调整：pyproject.toml

变更类型：文档更新 + 配置调整
建议版本递增：patch (3.0.0-alpha -> 3.0.0-alpha)

✓ 已更新 VERSION 文件：3.0.0-alpha
✓ 已更新 pyproject.toml: 3.0.0-alpha
✓ 已同步 45 个 Markdown 文件

新版本号：3.0.0-alpha
============================================================
```

### 示例 2：交互式确认

```bash
$ python tools/auto_version_control.py --interactive

检测到变更，请确认版本递增级别:
  1) patch (3.0.0-alpha -> 3.0.0-alpha) - 推荐
  2) minor (3.0.0-alpha -> 3.0.0-alpha)
  3) major (3.0.0-alpha -> 3.0.0-alpha)
  4) skip (跳过本次更新)

请选择 [1-4]: 1

✓ 版本已更新为 3.0.0-alpha
```

---

## 🚀 高级功能

### 1. Git 集成

自动读取最近的 Git commit 信息，智能判断变更类型：

```python
# 分析 commit message
if "feat:" in commit_message:
    return "minor"
elif "fix:" in commit_message:
    return "patch"
elif "BREAKING CHANGE" in commit_message:
    return "major"
```

### 2. 变更文件分析

智能识别修改的文件类型：

```python
# 核心架构文件
CORE_FILES = [
    "src/necorag.py",
    "src/core/",
    "interface/"
]

# 新增功能文件
if file_status == "A" and "src/" in file_path:
    change_type = "feature"

# Bug 修复
if "fix" in commit_message.lower():
    change_type = "bugfix"
```

### 3. 自动生成更新日志

```markdown
## [3.0.0-alpha] - 2026-03-19

### 📝 文档更新
- README.md - 更新版本号说明
- QUICKSTART.md - 添加版本管理命令

### 🔧 配置调整  
- pyproject.toml - 依赖版本更新

### 📊 统计
- 修改文件：3 个
- 影响范围：文档 + 配置
- 递增类型：patch
```

---

## ⚙️ 配置选项

在 `tools/auto_version_config.json` 中配置：

```json
{
  "auto_mode": true,
  "interactive": false,
  "dry_run": false,
  "commit_changes": true,
  "generate_changelog": true,
  "exclude_patterns": [
    "*.log",
    "*.tmp",
    ".git/",
    "__pycache__/"
  ],
  "core_files": [
    "src/necorag.py",
    "src/core/",
    "interface/"
  ]
}
```

---

## 📖 相关文件

- `tools/auto_version_control.py` - 主脚本
- `tools/auto_version_config.json` - 配置文件
- `VERSION` - 版本号文件
- `CHANGELOG.md` - 更新日志

---

<div align="center">

**让版本管理完全自动化！** 🚀

</div>
