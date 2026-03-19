# Code Count 指令使用指南

## 📋 概述

`code-count` 是 NecoRAG 项目的代码行数统计指令，可以：
- ✅ 自动读取项目版本号（从 VERSION 文件）
- ✅ 添加精确的时间戳
- ✅ 统计各类文件的行数和占比
- ✅ 区分代码行、空行、注释行
- ✅ 导出带版本号的 Markdown 报告

## 🚀 快速开始

### 方法一：使用 Python 脚本

```bash
# 在项目根目录执行
python tools/code-count.py -p ..

# 或在 tools 目录执行
cd tools
python code-count.py -p ..
```

### 方法二：使用 Shell 脚本（推荐）

```bash
# 在项目根目录执行
bash tools/code-count.sh -p ..

# 或直接调用
./tools/code-count.sh -p ..
```

## 📖 参数说明

### Python 脚本参数

```bash
python tools/code-count.py [选项]

选项:
  -p, --path PATH      项目根目录路径 (默认：..)
  -o, --output [FILE]  导出 Markdown 报告
                       不指定文件名则自动生成
  -v, --verbose        显示详细信息
  -h, --help           显示帮助信息
```

### Shell 脚本参数

```bash
bash tools/code-count.sh [选项]

选项:
  -p PATH    项目根目录路径 (默认：..)
  -o [FILE]  导出 Markdown 报告文件名
             不加参数则自动生成带时间戳的文件名
  -v         显示详细信息
  -h         显示帮助信息
```

## 💡 使用示例

### 1️⃣ 基础统计

```bash
# 统计整个项目
python tools/code-count.py -p ..

# 或使用 Shell 脚本
bash tools/code-count.sh
```

**输出示例：**
```
======================================================================
📊 NecoRAG 项目代码统计报告
======================================================================
⏰ 统计时间：2026-03-19 12:21:45
🏷️  项目版本：v3.2.0-alpha
======================================================================

📁 文件统计
----------------------------------------------------------------------
  总文件数：     537
  代码文件数：   522
  二进制文件数： 1
  其他文件数：   14

📝 代码行数统计
----------------------------------------------------------------------
  总行数：       205,667
  代码行数：     163,124
  空行数：       34,042
  注释行数：     8,501

  📊 行数比例:
    代码行占比：   79.3%
    空行占比：     16.6%
    注释行占比：   4.1%
```

### 2️⃣ 导出 Markdown 报告

```bash
# 自动生成带版本号和时问戳的文件名
python tools/code-count.py -p .. -o

# 或
bash tools/code-count.sh -o

# 生成的文件名为：code_count_v3.2.0-alpha_20260319_122145.md
```

### 3️⃣ 指定输出文件名

```bash
# Python 脚本
python tools/code-count.py -p .. -o my_report.md

# Shell 脚本
bash tools/code-count.sh -o my_report.md
```

### 4️⃣ 统计特定目录

```bash
# 统计核心源码
python tools/code-count.py -p src

# 统计测试代码
python tools/code-count.py -p tests

# 统计文档
python tools/code-count.py -p wiki
```

### 5️⃣ 显示详细信息

```bash
# Python 脚本
python tools/code-count.py -p .. -v

# Shell 脚本
bash tools/code-count.sh -v
```

## 📊 输出内容详解

### 终端输出包含：

1. **版本信息**
   ```
   🏷️  项目版本：v3.2.0-alpha
   ```
   - 自动从 `VERSION` 文件读取
   - 如果找不到 VERSION 文件，显示为 "unknown"

2. **时间戳**
   ```
   ⏰ 统计时间：2026-03-19 12:21:45
   ```
   - 格式：`YYYY-MM-DD HH:MM:SS`

3. **文件统计**
   - 总文件数
   - 代码文件数（.py, .js, .ts 等）
   - 二进制文件数（.png, .jpg, .pdf 等）
   - 其他文件数

4. **代码行数统计**
   - 总行数
   - 代码行数（实际逻辑代码）
   - 空行数
   - 注释行数
   - 各类型行数占比

5. **文件类型分布**
   - Top 15 文件类型
   - 每种类型的文件数量和占比
   - 平均每个文件的行数

6. **代码行数分布**
   - Top 10 代码类型
   - 每种类型的总行数和占比
   - 平均每个文件的行数

### Markdown 报告包含：

- 完整的统计表格
- 美观的 Markdown 格式
- 版本号和时问戳
- 可用于文档归档

## 🔧 高级用法

### 批量统计多个模块

```bash
#!/bin/bash

echo "=== 统计核心源码 ==="
python tools/code-count.py -p src -o src_stats.md

echo "=== 统计测试代码 ==="
python tools/code-count.py -p tests -o tests_stats.md

echo "=== 统计文档 ==="
python tools/code-count.py -p wiki -o wiki_stats.md
```

### 定期统计并归档

```bash
#!/bin/bash

# 创建月度报告目录
mkdir -p reports/$(date +%Y-%m)

# 统计并保存报告
python tools/code-count.py -p .. \
  -o reports/$(date +%Y-%m)/code_count_$(date +%Y%m%d).md

echo "报告已保存到：reports/$(date +%Y-%m)/"
```

### 对比历史数据

```bash
#!/bin/bash

# 获取当前统计
current=$(python tools/code-count.py -p .. 2>&1 | grep "总行数" | awk '{print $2}' | tr -d ',')

# 读取上次统计
last=$(cat reports/last_count.txt)

# 计算增长
diff=$((current - last))
percent=$(echo "scale=2; $diff * 100 / $last" | bc)

echo "代码行数变化："
echo "  上次：$last"
echo "  当前：$current"
echo "  增长：$diff ($percent%)"

# 更新记录
echo $current > reports/last_count.txt
```

## 📈 实际应用场景

### 场景 1：版本发布报告

在每个版本发布前运行：

```bash
# 发布新版本
python tools/code-count.py -p .. -o release_v3.0.0.md

# 将报告添加到发布说明中
cat release_v3.0.0.md >> RELEASE_NOTES.md
```

### 场景 2：项目进度追踪

每周/每月统计一次：

```bash
# 添加到 crontab
0 9 * * 1 bash /path/to/tools/code-count.sh -o weekly_report.md
```

### 场景 3：代码质量分析

分析注释率和代码密度：

```bash
# 运行统计
python tools/code-count.py -p ..

# 查看输出中的关键指标
# - 注释行占比（建议 8-12%）
# - 平均每文件行数（建议 <500 行）
```

## 🎯 最佳实践

### 1. 定期统计

建议在以下时机运行：
- ✅ 每个版本发布前
- ✅ 每月月底总结
- ✅ 重大重构前后
- ✅ 项目里程碑节点

### 2. 报告命名规范

推荐使用统一的命名格式：

```bash
# 按版本命名
code_count_v{version}_{timestamp}.md
# 例如：code_count_v3.2.0-alpha_20260319_122145.md

# 按日期命名
code_count_{YYYYMMDD}.md
# 例如：code_count_20260319.md
```

### 3. 报告归档结构

```
reports/
├── code_stats/
│   ├── 2026-03/
│   │   ├── code_count_20260319.md
│   │   └── code_count_20260326.md
│   └── 2026-04/
│       └── code_count_20260402.md
└── releases/
    ├── release_v1.0.0.md
    ├── release_v2.0.0.md
    └── release_v3.0.0.md
```

## ⚠️ 注意事项

### 1. 版本号来源

确保项目根目录有 `VERSION` 文件：
```
# VERSION 文件内容示例
3.2.0-alpha
```

如果找不到 VERSION 文件，工具会显示版本号为 "unknown"。

### 2. 统计准确性

以下情况可能影响统计准确性：
- 多行注释可能只统计第一行
- 字符串中的注释标记可能被误计
- 建议作为参考指标而非绝对值

### 3. 性能考虑

- 大文件（>10MB）可能影响统计速度
- 大量小文件也会增加处理时间
- 建议使用 `-v` 参数查看详细进度

### 4. 忽略规则

工具会自动忽略以下目录：
- `__pycache__`
- `.git`
- `.vscode`
- `.idea`
- `node_modules`
- `build`, `dist`, `target`
- `venv`, `.venv`
- `.env`, `.env.local`

## 🔗 相关文件

| 文件 | 说明 |
|------|------|
| `tools/code-count.py` | Python 主脚本 |
| `tools/code-count.sh` | Bash 快速启动脚本 |
| `tools/CODE_COUNT_README.md` | 详细使用文档 |
| `VERSION` | 项目版本号文件 |

## 💡 故障排查

### 问题 1：找不到 Python

**错误信息：**
```
❌ 错误：找不到 Python
```

**解决方案：**
```bash
# 检查 Python 是否安装
python --version
# 或
python3 --version

# 如果没有安装，先安装 Python 3.7+
```

### 问题 2：权限不足

**错误信息：**
```
zsh: permission denied: ./code-count.sh
```

**解决方案：**
```bash
# 添加执行权限
chmod +x tools/code-count.sh

# 或使用 bash 运行
bash tools/code-count.sh
```

### 问题 3：路径不存在

**错误信息：**
```
❌ 错误：路径不存在 - /some/path
```

**解决方案：**
```bash
# 检查路径是否正确
ls -la /some/path

# 使用绝对路径
python tools/code-count.py -p /absolute/path/to/project
```

## 🆚 与其他工具对比

### vs `cloc`

| 特性 | code-count.py | cloc |
|------|--------------|------|
| 版本号集成 | ✅ 自动读取 | ❌ 无 |
| 时间戳 | ✅ 精确到秒 | ⚠️ 需要额外参数 |
| Markdown 导出 | ✅ 内置支持 | ❌ 需要额外处理 |
| 多语言支持 | ✅ 20+ 种 | ✅ 100+ 种 |
| 速度 | ⚡ 快 | ⚡⚡ 更快 |

### vs `tokei`

| 特性 | code-count.py | tokei |
|------|--------------|-------|
| 版本号集成 | ✅ 自动读取 | ❌ 无 |
| Rust 实现 | ❌ Python | ✅ Rust |
| 速度 | ⚡ 快 | ⚡⚡⚡ 极快 |
| 自定义输出 | ✅ 灵活 | ⚠️ 有限 |

## 📞 获取帮助

如遇到其他问题：

1. 查看详细文档：`tools/CODE_COUNT_README.md`
2. 运行帮助命令：`python tools/code-count.py -h`
3. 使用详细模式：`python tools/code-count.py -v`

---

**NecoRAG Tools** © 2026  
*最后更新：2026-03-19*
