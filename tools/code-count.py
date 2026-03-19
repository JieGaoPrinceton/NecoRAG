#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NecoRAG 代码行数统计指令
统计项目代码行数，带版本号和时问戳
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import re


def get_version() -> str:
    """获取项目版本号"""
    version_file = Path(__file__).parent.parent / "VERSION"
    
    if not version_file.exists():
        return "unknown"
    
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            version = f.read().strip()
        return version
    except Exception as e:
        print(f"⚠️  读取 VERSION 文件失败：{e}")
        return "unknown"


def count_lines_in_file(file_path: Path) -> tuple:
    """
    统计单个文件的行数
    
    Returns:
        tuple: (总行数，代码行数，空行数，注释行数)
    """
    # 代码文件扩展名
    code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
                       '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
                       '.sql', '.sh', '.bash', '.ps1', '.yaml', '.yml', '.json', '.xml',
                       '.html', '.css', '.scss', '.sass', '.less', '.md', '.rst', '.txt'}
    
    # 二进制文件扩展名（不统计行数）
    binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
                         '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                         '.zip', '.tar', '.gz', '.rar', '.7z', '.exe', '.dll', '.so',
                         '.pyc', '.pyo', '.class', '.jar', '.war', '.ear'}
    
    ext = file_path.suffix.lower()
    
    # 二进制文件不统计
    if ext in binary_extensions:
        return (0, 0, 0, 0, 'binary')
    
    # 非代码文件只统计总行数
    if ext not in code_extensions:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            return (len(lines), 0, 0, 0, 'other')
        except:
            return (0, 0, 0, 0, 'other')
    
    # 统计代码文件
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        blank_lines = 0
        comment_lines = 0
        code_lines = 0
        
        for line in lines:
            stripped = line.strip()
            
            # 空行
            if not stripped:
                blank_lines += 1
                continue
            
            # 注释判断（根据文件类型）
            is_comment = False
            
            if ext == '.py':
                if stripped.startswith('#'):
                    is_comment = True
                elif stripped.startswith('"""') or stripped.startswith("'''"):
                    is_comment = True
            elif ext in ['.js', '.ts', '.jsx', '.tsx']:
                if stripped.startswith('//') or stripped.startswith('/*') or stripped.endswith('*/'):
                    is_comment = True
            elif ext in ['.java', '.cpp', '.c', '.h', '.cs']:
                if stripped.startswith('//') or stripped.startswith('/*') or stripped.endswith('*/'):
                    is_comment = True
            elif ext in ['.html', '.xml']:
                if stripped.startswith('<!--') and stripped.endswith('-->'):
                    is_comment = True
            elif ext in ['.yaml', '.yml']:
                if stripped.startswith('#'):
                    is_comment = True
            elif ext == '.sql':
                if stripped.startswith('--') or stripped.startswith('/*') or stripped.endswith('*/'):
                    is_comment = True
            elif ext in ['.sh', '.bash']:
                if stripped.startswith('#'):
                    is_comment = True
            
            if is_comment:
                comment_lines += 1
            else:
                code_lines += 1
        
        return (total_lines, code_lines, blank_lines, comment_lines, 'code')
    
    except Exception as e:
        return (0, 0, 0, 0, 'error')


def scan_directory(root_path: Path, ignore_patterns=None):
    """
    扫描目录统计代码行数
    
    Args:
        root_path: 根目录路径
        ignore_patterns: 忽略的模式列表
    
    Returns:
        dict: 统计结果
    """
    if ignore_patterns is None:
        ignore_patterns = {
            '__pycache__', '.git', '.vscode', '.idea', '.DS_Store',
            'node_modules', 'build', 'dist', 'target', 'venv', '.venv',
            '.env', '.env.local', '.gitignore', '.dockerignore'
        }
    
    stats = {
        'total_files': 0,
        'code_files': 0,
        'binary_files': 0,
        'other_files': 0,
        'total_lines': 0,
        'code_lines': 0,
        'blank_lines': 0,
        'comment_lines': 0,
        'files_by_type': {},
        'lines_by_type': {}
    }
    
    # 遍历目录
    for root, dirs, files in os.walk(root_path):
        # 过滤忽略的目录
        dirs[:] = [d for d in dirs if d not in ignore_patterns]
        
        root_path = Path(root)
        
        for file in files:
            # 跳过隐藏文件
            if file.startswith('.') and file not in ['.env.example', '.dockerignore']:
                continue
            
            file_path = root_path / file
            
            # 统计文件
            total, code, blank, comment, file_type = count_lines_in_file(file_path)
            
            stats['total_files'] += 1
            
            if file_type == 'binary':
                stats['binary_files'] += 1
            elif file_type == 'other':
                stats['other_files'] += 1
            elif file_type == 'code':
                stats['code_files'] += 1
                stats['total_lines'] += total
                stats['code_lines'] += code
                stats['blank_lines'] += blank
                stats['comment_lines'] += comment
                
                # 按扩展名统计
                ext = file_path.suffix.lower() or '(no extension)'
                stats['files_by_type'][ext] = stats['files_by_type'].get(ext, 0) + 1
                stats['lines_by_type'][ext] = stats['lines_by_type'].get(ext, 0) + total
            else:
                stats['other_files'] += 1
    
    return stats


def print_statistics(stats: dict, version: str):
    """打印统计结果"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print("\n" + "=" * 70)
    print(f"📊 NecoRAG 项目代码统计报告")
    print("=" * 70)
    print(f"⏰ 统计时间：{timestamp}")
    print(f"🏷️  项目版本：v{version}")
    print("=" * 70)
    
    # 基本统计
    print(f"\n📁 文件统计")
    print("-" * 70)
    print(f"  总文件数：     {stats['total_files']:,}")
    print(f"  代码文件数：   {stats['code_files']:,}")
    print(f"  二进制文件数： {stats['binary_files']:,}")
    print(f"  其他文件数：   {stats['other_files']:,}")
    
    # 代码行数统计
    print(f"\n📝 代码行数统计")
    print("-" * 70)
    print(f"  总行数：       {stats['total_lines']:,}")
    print(f"  代码行数：     {stats['code_lines']:,}")
    print(f"  空行数：       {stats['blank_lines']:,}")
    print(f"  注释行数：     {stats['comment_lines']:,}")
    
    if stats['total_lines'] > 0:
        code_ratio = (stats['code_lines'] / stats['total_lines']) * 100
        blank_ratio = (stats['blank_lines'] / stats['total_lines']) * 100
        comment_ratio = (stats['comment_lines'] / stats['total_lines']) * 100
        
        print(f"\n  📊 行数比例:")
        print(f"    代码行占比：   {code_ratio:.1f}%")
        print(f"    空行占比：     {blank_ratio:.1f}%")
        print(f"    注释行占比：   {comment_ratio:.1f}%")
    
    # 文件类型分布
    if stats['files_by_type']:
        print(f"\n📋 文件类型分布 (Top 15)")
        print("-" * 70)
        sorted_types = sorted(
            stats['files_by_type'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:15]
        
        for ext, count in sorted_types:
            lines = stats['lines_by_type'].get(ext, 0)
            percentage = (count / stats['total_files']) * 100
            avg_lines = lines / max(count, 1)
            print(f"  {ext:15} : {count:5,} 个文件 ({percentage:5.1f}%) - {lines:7,} 行 (均 {avg_lines:.0f} 行/文件)")
    
    # 代码行数分布
    if stats['lines_by_type']:
        print(f"\n📈 代码行数分布 (Top 10)")
        print("-" * 70)
        sorted_lines = sorted(
            stats['lines_by_type'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        for ext, lines in sorted_lines:
            if lines > 0:
                percentage = (lines / stats['total_lines']) * 100
                file_count = stats['files_by_type'].get(ext, 1)
                avg_lines = lines / file_count
                print(f"  {ext:15} : {lines:7,} 行 ({percentage:5.1f}%) - 平均 {avg_lines:.0f} 行/文件")
    
    print("\n" + "=" * 70)
    print(f"✨ 统计完成 | v{version} | {timestamp}")
    print("=" * 70 + "\n")


def export_to_markdown(stats: dict, version: str, output_path: str = None):
    """导出为 Markdown 格式"""
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"code_count_v{version}_{timestamp}.md"
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    md_content = f"""# NecoRAG 项目代码统计报告

**统计时间**: {timestamp}  
**项目版本**: v{version}

---

## 📊 基本统计

| 统计项 | 数值 |
|--------|------|
| 总文件数 | {stats['total_files']:,} |
| 代码文件数 | {stats['code_files']:,} |
| 二进制文件数 | {stats['binary_files']:,} |
| 其他文件数 | {stats['other_files']:,} |

---

## 📝 代码行数统计

| 类型 | 行数 | 占比 |
|------|------|------|
| 总行数 | {stats['total_lines']:,} | 100% |
| 代码行数 | {stats['code_lines']:,} | {(stats['code_lines'] / max(stats['total_lines'], 1)) * 100:.1f}% |
| 空行数 | {stats['blank_lines']:,} | {(stats['blank_lines'] / max(stats['total_lines'], 1)) * 100:.1f}% |
| 注释行数 | {stats['comment_lines']:,} | {(stats['comment_lines'] / max(stats['total_lines'], 1)) * 100:.1f}% |

---

## 📋 文件类型分布

| 文件扩展名 | 文件数量 | 占比 | 总行数 | 平均每文件 |
|------------|----------|------|--------|-----------|
"""
    
    sorted_types = sorted(
        stats['files_by_type'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:20]
    
    for ext, count in sorted_types:
        lines = stats['lines_by_type'].get(ext, 0)
        percentage = (count / max(stats['total_files'], 1)) * 100
        avg_lines = lines / max(count, 1)
        md_content += f"| {ext} | {count:,} | {percentage:.1f}% | {lines:,} | {avg_lines:.0f} |\n"
    
    md_content += f"\n---\n\n*本报告由 NecoRAG Code Count 工具自动生成 (v{version})*\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"📄 Markdown 报告已导出到：{output_path}")
    return output_path


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='NecoRAG 代码行数统计工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python code-count.py                    # 统计当前目录
  python code-count.py -p /path/to/src    # 统计指定目录
  python code-count.py -o report.md       # 导出 Markdown 报告
        """
    )
    
    parser.add_argument(
        '-p', '--path',
        default='..',
        help='项目根目录路径 (默认：../ 即项目根目录)'
    )
    
    parser.add_argument(
        '-o', '--output',
        nargs='?',
        const='auto',
        help='导出 Markdown 报告 (可选指定文件名)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细信息'
    )
    
    args = parser.parse_args()
    
    try:
        # 获取版本号
        version = get_version()
        
        # 解析路径
        target_path = Path(args.path).resolve()
        
        if not target_path.exists():
            print(f"❌ 错误：路径不存在 - {target_path}")
            sys.exit(1)
        
        print(f"\n🔍 开始扫描项目：{target_path}")
        print(f"🏷️  使用版本：v{version}\n")
        
        # 执行统计
        stats = scan_directory(target_path)
        
        # 打印结果
        print_statistics(stats, version)
        
        # 导出 Markdown（如果指定了输出）
        if args.output:
            if args.output == 'auto':
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"code_count_v{version}_{timestamp}.md"
            else:
                output_file = args.output
            
            export_to_markdown(stats, version, output_file)
        
        # 返回成功
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 统计过程中发生错误：{e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
