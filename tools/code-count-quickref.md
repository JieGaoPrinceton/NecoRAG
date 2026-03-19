# Code Count 指令 - 快速参考

## 🎯 一句话介绍

`code-count` 是 NecoRAG 项目的代码统计工具，**自动带版本号和时问戳**。

## ⚡ 30 秒上手

### 最简单用法

```bash
# 方法 1：Python 脚本
python tools/code-count.py -p ..

# 方法 2：Shell 脚本（推荐）
bash tools/code-count.sh -p ..
```

### 导出报告

```bash
# 自动生成带版本号的 Markdown 文件
python tools/code-count.py -p .. -o

# 生成文件名示例：code_count_v3.1.0-alpha_20260319_122145.md
```

## 📋 常用命令速查

| 需求 | 命令 |
|------|------|
| 基础统计 | `python tools/code-count.py -p ..` |
| 导出报告 | `python tools/code-count.py -p .. -o` |
| 指定文件名 | `python tools/code-count.py -p .. -o report.md` |
| 统计特定目录 | `python tools/code-count.py -p src` |
| 显示帮助 | `python tools/code-count.py -h` |

## 🎨 输出示例

```
======================================================================
📊 NecoRAG 项目代码统计报告
======================================================================
⏰ 统计时间：2026-03-19 12:21:45
🏷️  项目版本：v3.1.0-alpha
======================================================================

📁 文件统计
----------------------------------------------------------------------
  总文件数：     537
  代码文件数：   522

📝 代码行数统计
----------------------------------------------------------------------
  总行数：       205,667
  代码行数：     163,124 (79.3%)
  空行数：       34,042 (16.6%)
  注释行数：     8,501 (4.1%)
```

## 📁 文件清单

创建的文件：
- ✅ `tools/code-count.py` - Python 主脚本
- ✅ `tools/code-count.sh` - Bash 快速启动脚本
- ✅ `tools/CODE_COUNT_README.md` - 详细文档
- ✅ `tools/CODE_COUNT_GUIDE.md` - 使用指南
- ✅ `tools/code-count-quickref.md` - 本文件

## 🔑 核心特性

1. **自动版本号** - 从 VERSION 文件读取
2. **精确时间戳** - 记录到秒级
3. **多格式输出** - 终端显示 + Markdown 导出
4. **智能分类** - 区分代码、空行、注释
5. **类型分布** - 按文件扩展名统计

## 💡 典型场景

### 场景 1：版本发布前统计

```bash
python tools/code-count.py -p .. -o release_v$(cat VERSION).md
```

### 场景 2：每周代码量追踪

```bash
# 每周一早上 9 点执行
0 9 * * 1 cd /path/to/project && python tools/code-count.py -p .. -o weekly_$(date +%Y%m%d).md
```

### 场景 3：对比重构前后

```bash
# 重构前
python tools/code-count.py -p .. -o before_refactor.md

# ... 进行重构 ...

# 重构后
python tools/code-count.py -p .. -o after_refactor.md

# 对比两个文件
diff before_refactor.md after_refactor.md
```

## ⚠️ 常见问题

**Q: 找不到 VERSION 文件怎么办？**  
A: 工具会显示版本号为 "unknown"，但不影响统计功能。

**Q: 如何统计特定类型的文件？**  
A: 修改脚本中的 `CODE_EXTENSIONS` 集合。

**Q: 如何忽略某些目录？**  
A: 修改脚本中的 `IGNORE_PATTERNS` 集合。

**Q: 统计结果准确吗？**  
A: 可作为参考指标，但多行注释等情况可能有误差。

## 📖 更多信息

- 详细文档：`tools/CODE_COUNT_README.md`
- 使用指南：`tools/CODE_COUNT_GUIDE.md`
- 项目根目录：运行 `python tools/code-count.py -h`

---

**快速开始，就这么简单！** ✨

*NecoRAG Tools © 2026*
