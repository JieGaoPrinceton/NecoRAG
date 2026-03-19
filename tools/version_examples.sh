#!/bin/bash
# NecoRAG 版本管理常用命令示例

echo "======================================"
echo "NecoRAG 版本管理示例"
echo "======================================"
echo ""

echo "1️⃣  查看当前版本"
echo "   python tools/version_manager.py show"
echo ""

echo "2️⃣  递增补丁号（小更新，如 1.9.0 -> 1.9.1）"
echo "   python tools/version_manager.py bump patch"
echo ""

echo "3️⃣  递增次版本号（新功能，如 1.9.0 -> 1.10.0）"
echo "   python tools/version_manager.py bump minor"
echo ""

echo "4️⃣  递增主版本号（重大变更，如 1.9.0 -> 2.0.0）"
echo "   python tools/version_manager.py bump major"
echo ""

echo "5️⃣  直接设置版本号"
echo "   python tools/version_manager.py set 1.10.0-alpha"
echo ""

echo "6️⃣  同步版本号到所有文件（预览模式）"
echo "   python tools/version_manager.py sync --dry-run"
echo ""

echo "7️⃣  同步版本号到所有文件（实际执行）"
echo "   python tools/version_manager.py sync"
echo ""

echo "======================================"
echo "标准发布流程示例："
echo "======================================"
echo ""
echo "# 1. 查看当前版本"
echo "python tools/version_manager.py show"
echo ""
echo "# 2. 递增版本号"
echo "python tools/version_manager.py bump minor"
echo ""
echo "# 3. 提交更改"
echo "git add VERSION pyproject.toml *.md"
echo 'git commit -m "chore: bump version to 1.10.0-alpha"'
echo ""
echo "# 4. 打标签（可选）"
echo "git tag v1.10.0-alpha"
echo "git push origin v1.10.0-alpha"
echo ""
echo "======================================"
