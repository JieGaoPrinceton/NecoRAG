---
description:统计本项目的代码行数，按照版本号，加上时间戳和版本号
---
#!/bin/bash

# 获取当前时间戳
timestamp=$(date "+%Y-%m-%d %H:%M:%S")

# 获取版本号（从git tag获取，如果没有则使用默认值）
version=$(git describe --tags --abbrev=0 2>/dev/null || echo "v3.2.0-alpha")

# 定义要统计的文件扩展名
extensions=("py" "md" "sh" "yaml" "yml" "json" "txt")

echo "========================================"
echo "代码统计报告"
echo "版本: $version"
echo "时间: $timestamp"
echo "========================================"

total_lines=0

for ext in "${extensions[@]}"; do
    count=$(find . -name "*.$ext" -not -path "./.git/*" -not -path "./.venv/*" -not -path "./venv/*" -not -path "./__pycache__/*" -not -path "./.qoder/*" | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
    if [ -n "$count" ] && [ "$count" != "0" ]; then
        printf "%-10s %s 行\n" ".$ext:" "$count"
        total_lines=$((total_lines + count))
    fi
done

echo "----------------------------------------"
echo "总计: $total_lines 行"
echo "========================================"
