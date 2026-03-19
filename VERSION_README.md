# NecoRAG 版本号管理

## 📋 快速使用

当前项目版本：**3.0.1-alpha**

### 查看当前版本

```bash
python tools/version_manager.py show
```

### 更新版本号

#### 递增补丁号（小更新）
```bash
python tools/version_manager.py bump patch
# 3.0.1-alpha -> 3.0.1-alpha
```

#### 递增次版本号（新功能）
```bash
python tools/version_manager.py bump minor
# 3.0.1-alpha -> 3.0.1-alpha
```

#### 递增主版本号（重大变更）
```bash
python tools/version_manager.py bump major
# 3.0.1-alpha -> 3.0.1-alpha
```

#### 直接设置版本
```bash
python tools/version_manager.py set 3.0.1-alpha
```

### 同步版本号到所有文件

```bash
# 实际执行
python tools/version_manager.py sync

# 预览模式（查看将更新哪些文件）
python tools/version_manager.py sync --dry-run
```

## 📁 文件说明

- **`VERSION`** - 版本号源文件（唯一数据源）
- **`pyproject.toml`** - Python 项目版本配置
- **`tools/version_manager.py`** - 版本管理工具
- **`tools/VERSION_MANAGER_GUIDE.md`** - 详细使用指南

## 🔄 自动更新范围

工具会自动更新项目中所有 Markdown 文件的版本号引用，包括：
- ✅ README.md
- ✅ QUICKSTART.md  
- ✅ CHANGELOG.md
- ✅ 所有模块的 README
- ✅ Wiki 文档
- ✅ 设计文档
- ✅ 其他所有 `.md` 文件

## 💡 标准工作流程

```bash
# 1. 发布新版本
python tools/version_manager.py bump minor

# 2. 验证更改（可选）
git status

# 3. 提交更改
git add VERSION pyproject.toml *.md
git commit -m "chore: bump version to 3.0.1-alpha"

# 4. 打标签（可选）
git tag v3.0.1-alpha
git push origin v3.0.1-alpha
```

## 📚 详细文档

查看 [tools/VERSION_MANAGER_GUIDE.md](tools/VERSION_MANAGER_GUIDE.md) 获取完整的使用指南。

---

**最后更新**: 2026-03-19 | **版本**: 3.0.1-alpha
