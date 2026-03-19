# NecoRAG 自动版本控制技能使用指南

## 🎯 技能概述

**技能名称**: Auto Version Control  
**功能**: 自动检测项目变更并智能更新版本号  
**触发时机**: 每次代码提交、配置变更或手动触发时

---

## ✨ 核心特性

### 1. 智能变更检测
- ✅ 基于 Git 状态分析未提交的变更
- ✅ 识别新增、修改、删除的文件
- ✅ 分析最近的 commit 信息
- ✅ 排除临时文件和日志

### 2. 自动版本递增
根据变更类型智能选择递增级别：

| 变更类型 | 触发条件 | 递增级别 | 示例 |
|---------|---------|---------|------|
| 🔴 重大重构 | 核心架构变更、BREAKING CHANGE | major | 3.0.0-alpha → 3.0.0-alpha |
| 🟢 新功能 | 新增模块、新功能实现 | minor | 3.0.0-alpha → 3.0.0-alpha |
| 🔵 Bug 修复 | 错误修复、性能优化 | patch | 3.0.0-alpha → 3.0.0-alpha |
| 📝 文档更新 | 仅修改文档 | patch | 3.0.0-alpha → 3.0.0-alpha |
| ⚙️ 配置调整 | 配置文件变更 | patch | 3.0.0-alpha → 3.0.0-alpha |

### 3. 批量同步
- 自动更新 `VERSION` 文件
- 同步 `pyproject.toml` 版本
- 更新所有 Markdown 文件中的版本号引用
- 生成更新日志（CHANGELOG.md）

---

## 🚀 使用方法

### 方式 1：命令行工具

```bash
# 基本用法（推荐）
python tools/auto_version_control.py

# 交互模式（需要确认）
python tools/auto_version_control.py -i

# 预览模式（查看将进行的更改）
python tools/auto_version_control.py --dry-run

# 完全自动模式（无需确认）
python tools/auto_version_control.py --auto
```

### 方式 2：Git Hook 自动触发

在 `.git/hooks/pre-commit` 中自动调用：

```bash
#!/bin/bash
# 执行自动版本控制
python tools/auto_version_control.py --auto

# 如果有更新，自动添加到暂存区
git add VERSION pyproject.toml *.md
```

### 方式 3：集成到开发流程

#### VS Code 任务配置

在 `.vscode/tasks.json` 中添加：

```json
{
    "label": "Auto Version Control",
    "type": "shell",
    "command": "python tools/auto_version_control.py",
    "group": "build",
    "presentation": {
        "reveal": "always",
        "panel": "new"
    }
}
```

#### PyCharm 外部工具

配置步骤：
1. Settings → Tools → External Tools
2. 添加新工具：
   - Name: Auto Version
   - Program: `python`
   - Arguments: `tools/auto_version_control.py`
   - Working directory: `$ProjectFileDir$`

---

## 💡 使用示例

### 示例 1：日常开发提交

```bash
# 1. 修改代码
vim src/necorag.py

# 2. 添加到暂存区
git add src/necorag.py

# 3. 准备提交
git commit -m "feat: add new retrieval strategy"

# 4. 自动版本控制会检测到变更并递增版本号
# 输出：
# 🔍 检测项目变更...
# 检测到 1 个文件变更:
#   ✏️ modified: 1 个文件
# 
# 📊 分析变更类型...
# 变更类型：🟢 新功能 (1 个文件)
# 建议更新：minor → 3.0.0-alpha
# 
# ✓ 已更新 VERSION 文件：3.0.0-alpha
# ✓ 已同步 45 个 Markdown 文件
```

### 示例 2：紧急 Bug 修复

```bash
# 快速修复并更新版本
python tools/auto_version_control.py --auto

# 输出：
# 🔍 检测项目变更...
# 变更类型：🔵 Bug 修复
# ✓ 版本已更新为：3.0.0-alpha
```

### 示例 3：大版本发布前检查

```bash
# 预览版本更新影响
python tools/auto_version_control.py --dry-run

# 输出：
# 📝 预览模式：将更新版本号为 3.0.0-alpha
# （不实际修改文件，仅查看将要发生的变化）
```

---

## ⚙️ 配置选项

配置文件位置：`tools/auto_version_config.json`

```json
{
  "auto_mode": true,          // 是否自动模式
  "interactive": false,       // 是否交互式确认
  "dry_run": false,           // 是否预览模式
  "commit_changes": true,     // 是否自动提交版本变更
  "generate_changelog": true, // 是否生成更新日志
  
  "exclude_patterns": [       // 排除的文件模式
    "*.log",
    "*.tmp",
    ".git/",
    "__pycache__/"
  ],
  
  "core_files": [             // 核心文件列表（修改触发 major 更新）
    "src/necorag.py",
    "src/core/",
    "interface/"
  ]
}
```

---

## 📊 工作流程

```
开始
  │
  ▼
检测项目变更 ──▶ 无变更 ──▶ 结束
  │
  ▼
分析变更类型
  │
  ├─▶ 重大重构 ──▶ major 递增
  ├─▶ 新功能 ────▶ minor 递增
  └─▶ Bug 修复 ──▶ patch 递增
  │
  ▼
计算新版本号
  │
  ▼
用户确认？─┬─▶ 是 ──▶ 执行更新
          │         ├─ 更新 VERSION
          │         ├─ 同步 pyproject.toml
          │         ├─ 更新所有 .md 文件
          │         └─ 生成 CHANGELOG
          │
          └─ 否 ──▶ 取消更新
```

---

## 🔧 高级功能

### 1. Git Commit 信息分析

自动读取最近的 commit 信息判断变更类型：

```python
# commit message 包含 "feat:" → minor 递增
# commit message 包含 "fix:" → patch 递增
# commit message 包含 "BREAKING CHANGE" → major 递增
```

### 2. 智能文件分类

根据修改的文件路径和类型自动判断：

```python
# src/core/ 下的修改 → 可能是 major
# src/features/ 新增 → minor
# docs/ 修改 → patch
# tests/ 修改 → patch
```

### 3. 自动生成更新日志

```markdown
## [3.0.0-alpha] - 2026-03-19

### 🟢 新功能 (3 个文件)

**修改文件**:
- `src/retrieval/smart_routing.py`
- `src/intent/analyzer.py`
- `README.md`

---
```

---

## 🛠️ 故障排查

### 问题 1：无法检测变更

**症状**: 显示"未检测到变更"但实际有修改

**解决方案**:
```bash
# 检查是否在 Git 仓库中
git status

# 如果不是 Git 仓库，初始化一个
git init
git add .
git commit -m "Initial commit"
```

### 问题 2：版本号格式错误

**症状**: `无效的版本号格式`

**解决方案**:
```bash
# 检查 VERSION 文件内容
cat VERSION

# 应该类似：3.0.0-alpha
# 如果格式不对，手动修正
echo "3.0.0-alpha" > VERSION
```

### 问题 3：同步失败

**症状**: 某些文件更新失败

**解决方案**:
```bash
# 检查文件权限
ls -la README.md

# 如果需要，修复权限
chmod 644 README.md

# 重新运行
python tools/auto_version_control.py
```

---

## 📈 最佳实践

### ✅ 推荐做法

1. **每次提交前都运行**
   - 确保版本号与代码状态一致
   - 自动生成更新记录

2. **使用交互模式进行重大更新**
   ```bash
   python tools/auto_version_control.py -i
   ```

3. **定期审查更新日志**
   - 保持日志清晰简洁
   - 删除不必要的细节

4. **在 CI/CD 中集成**
   - 自动验证版本号
   - 确保发布流程标准化

### ❌ 避免的做法

1. **不要跳过版本更新**
   - 即使是很小的修改也应该更新版本

2. **不要手动修改版本号**
   - 始终使用自动化工具
   - 避免人为错误

3. **不要忘记提交版本文件**
   ```bash
   git add VERSION pyproject.toml
   ```

---

## 🎉 总结

自动版本控制技能让版本管理变得：
- ✅ **自动化** - 无需手动操作
- ✅ **智能化** - 根据变更类型自动判断
- ✅ **标准化** - 遵循语义化版本规范
- ✅ **可追溯** - 自动生成更新日志

**从现在开始**，每次提交只需一行命令：

```bash
python tools/auto_version_control.py --auto
```

整个项目的版本号会自动更新！🚀

---

**创建时间**: 2026-03-19  
**版本**: 3.0.0-alpha  
**作者**: NecoRAG Team
