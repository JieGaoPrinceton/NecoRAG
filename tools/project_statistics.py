#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NecoRAG 项目统计工具
统计整个项目的文件数量和代码行数
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import argparse
from collections import defaultdict


class ProjectStatistics:
    """项目统计器"""
    
    # 常见的代码文件扩展名
    CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
        '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
        '.sql', '.sh', '.bash', '.ps1', '.yaml', '.yml', '.json', '.xml',
        '.html', '.css', '.scss', '.sass', '.less', '.md', '.rst', '.txt'
    }
    
    # 二进制文件扩展名
    BINARY_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.tar', '.gz', '.rar', '.7z', '.exe', '.dll', '.so',
        '.pyc', '.pyo', '.class', '.jar', '.war', '.ear'
    }
    
    # 忽略的目录和文件
    IGNORE_PATTERNS = {
        '__pycache__', '.git', '.vscode', '.idea', '.DS_Store',
        'node_modules', 'build', 'dist', 'target', 'venv', '.venv',
        '.env', '.env.local', '.gitignore', '.dockerignore'
    }
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.stats = {
            'total_files': 0,
            'code_files': 0,
            'binary_files': 0,
            'other_files': 0,
            'total_lines': 0,
            'code_lines': 0,
            'blank_lines': 0,
            'comment_lines': 0,
            'files_by_extension': defaultdict(int),
            'lines_by_extension': defaultdict(int),
            'directories': set()
        }
    
    def is_ignored(self, path: Path) -> bool:
        """检查路径是否应该被忽略"""
        # 检查路径中的任何部分是否匹配忽略模式
        path_parts = path.parts[len(self.project_root.parts):]
        for part in path_parts:
            if part in self.IGNORE_PATTERNS:
                return True
        return False
    
    def get_file_type(self, file_path: Path) -> str:
        """确定文件类型"""
        ext = file_path.suffix.lower()
        
        if ext in self.CODE_EXTENSIONS:
            return 'code'
        elif ext in self.BINARY_EXTENSIONS:
            return 'binary'
        else:
            return 'other'
    
    def count_lines(self, file_path: Path) -> Tuple[int, int, int]:
        """
        统计文件行数
        返回: (总行数, 代码行数, 空行数, 注释行数)
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except (UnicodeDecodeError, PermissionError):
            # 无法读取的文件视为二进制文件
            return (0, 0, 0, 0)
        
        total_lines = len(lines)
        blank_lines = 0
        comment_lines = 0
        code_lines = 0
        
        ext = file_path.suffix.lower()
        
        for line in lines:
            stripped_line = line.strip()
            
            # 统计空行
            if not stripped_line:
                blank_lines += 1
                continue
            
            # 根据文件类型判断注释
            is_comment = False
            
            if ext == '.py':
                # Python 注释
                if stripped_line.startswith('#'):
                    is_comment = True
                elif stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                    is_comment = True
            elif ext in ['.js', '.ts', '.jsx', '.tsx']:
                # JavaScript/TypeScript 注释
                if stripped_line.startswith('//') or stripped_line.startswith('/*') or stripped_line.endswith('*/'):
                    is_comment = True
            elif ext in ['.java', '.cpp', '.c', '.h', '.cs']:
                # C系语言注释
                if stripped_line.startswith('//') or stripped_line.startswith('/*') or stripped_line.endswith('*/'):
                    is_comment = True
            elif ext in ['.html', '.xml']:
                # HTML/XML 注释
                if stripped_line.startswith('<!--') and stripped_line.endswith('-->'):
                    is_comment = True
            elif ext in ['.yaml', '.yml']:
                # YAML 注释
                if stripped_line.startswith('#'):
                    is_comment = True
            elif ext == '.sql':
                # SQL 注释
                if stripped_line.startswith('--') or stripped_line.startswith('/*') or stripped_line.endswith('*/'):
                    is_comment = True
            elif ext in ['.sh', '.bash']:
                # Shell 脚本注释
                if stripped_line.startswith('#'):
                    is_comment = True
            
            if is_comment:
                comment_lines += 1
            else:
                code_lines += 1
        
        return (total_lines, code_lines, blank_lines, comment_lines)
    
    def scan_project(self):
        """扫描项目并统计数据"""
        print(f"🔍 正在扫描项目：{self.project_root}")
        print("-" * 50)
            
        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)
                
            # 跳过隐藏目录和忽略的目录（但保留 .qoder 等配置目录用于统计）
            dirs[:] = [d for d in dirs if not d.startswith('.') or d == '.qoder']
            dirs[:] = [d for d in dirs if d not in self.IGNORE_PATTERNS]
                
            if self.is_ignored(root_path):
                continue
                
            # 记录目录
            rel_dir = root_path.relative_to(self.project_root)
            if rel_dir != Path('.'):
                self.stats['directories'].add(str(rel_dir))
                
            # 处理文件
            for file in files:
                if file.startswith('.') and file not in ['.env.example', '.dockerignore']:
                    continue
                        
                file_path = root_path / file
                    
                if self.is_ignored(file_path):
                    continue
                    
                self.stats['total_files'] += 1
                file_type = self.get_file_type(file_path)
                ext = file_path.suffix.lower() or '(no extension)'
                    
                self.stats['files_by_extension'][ext] += 1
                    
                if file_type == 'code':
                    self.stats['code_files'] += 1
                    total_lines, code_lines, blank_lines, comment_lines = self.count_lines(file_path)
                        
                    self.stats['total_lines'] += total_lines
                    self.stats['code_lines'] += code_lines
                    self.stats['blank_lines'] += blank_lines
                    self.stats['comment_lines'] += comment_lines
                    self.stats['lines_by_extension'][ext] += total_lines
                        
                elif file_type == 'binary':
                    self.stats['binary_files'] += 1
                else:
                    self.stats['other_files'] += 1
    
    def print_statistics(self):
        """打印统计结果"""
        print("\n📊 项目统计结果")
        print("=" * 50)
        
        # 基本统计
        print(f"📁 总文件数: {self.stats['total_files']:,}")
        print(f"📝 代码文件: {self.stats['code_files']:,}")
        print(f"💾 二进制文件: {self.stats['binary_files']:,}")
        print(f"📄 其他文件: {self.stats['other_files']:,}")
        print(f"📂 目录数量: {len(self.stats['directories']):,}")
        
        print("\n📈 代码行数统计")
        print("-" * 30)
        print(f"totalCount: {self.stats['total_lines']:,}")
        print(f"代码行数: {self.stats['code_lines']:,}")
        print(f"空行数: {self.stats['blank_lines']:,}")
        print(f"注释行数: {self.stats['comment_lines']:,}")
        
        if self.stats['total_lines'] > 0:
            code_ratio = (self.stats['code_lines'] / self.stats['total_lines']) * 100
            blank_ratio = (self.stats['blank_lines'] / self.stats['total_lines']) * 100
            comment_ratio = (self.stats['comment_lines'] / self.stats['total_lines']) * 100
            print(f"\n📊 行数比例:")
            print(f"代码行占比: {code_ratio:.1f}%")
            print(f"空行占比: {blank_ratio:.1f}%")
            print(f"注释行占比: {comment_ratio:.1f}%")
        
        # 按文件类型统计
        if self.stats['files_by_extension']:
            print(f"\n📁 文件类型分布")
            print("-" * 30)
            sorted_extensions = sorted(
                self.stats['files_by_extension'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for ext, count in sorted_extensions[:15]:  # 显示前15个
                percentage = (count / self.stats['total_files']) * 100
                print(f"{ext:12} : {count:4,} 个文件 ({percentage:5.1f}%)")
            
            if len(sorted_extensions) > 15:
                remaining = len(sorted_extensions) - 15
                remaining_count = sum(count for _, count in sorted_extensions[15:])
                print(f"... 还有 {remaining} 种文件类型 ({remaining_count} 个文件)")
        
        # 按代码行数统计
        if self.stats['lines_by_extension']:
            print(f"\n📝 代码行数分布")
            print("-" * 30)
            sorted_lines = sorted(
                self.stats['lines_by_extension'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for ext, lines in sorted_lines[:10]:  # 显示前10个
                if lines > 0:
                    percentage = (lines / self.stats['total_lines']) * 100
                    avg_lines = lines / max(self.stats['files_by_extension'][ext], 1)
                    print(f"{ext:12} : {lines:6,} 行 ({percentage:5.1f}%) - 平均 {avg_lines:.1f} 行/文件")
        
        # 目录结构摘要
        if self.stats['directories']:
            print(f"\n📂 主要目录")
            print("-" * 30)
            main_dirs = [d for d in self.stats['directories'] if '/' not in d]
            for dir_name in sorted(main_dirs)[:10]:
                print(f"  {dir_name}/")
            
            if len(main_dirs) > 10:
                print(f"  ... 还有 {len(main_dirs) - 10} 个目录")
    
    def export_csv(self, filename: str = "project_statistics.csv"):
        """导出统计结果到 CSV文件"""
        import csv
            
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
                
            # 基本统计
            writer.writerow(['统计项', '数值'])
            writer.writerow(['总文件数', self.stats['total_files']])
            writer.writerow(['代码文件数', self.stats['code_files']])
            writer.writerow(['二进制文件数', self.stats['binary_files']])
            writer.writerow(['其他文件数', self.stats['other_files']])
            writer.writerow(['目录数量', len(self.stats['directories'])])
            writer.writerow([])
                
            # 行数统计
            writer.writerow(['行数统计', '数值'])
            writer.writerow(['总行数', self.stats['total_lines']])
            writer.writerow(['代码行数', self.stats['code_lines']])
            writer.writerow(['空行数', self.stats['blank_lines']])
            writer.writerow(['注释行数', self.stats['comment_lines']])
            writer.writerow([])
                
            # 文件类型分布
            writer.writerow(['文件扩展名', '文件数量', '行数'])
            sorted_extensions = sorted(
                self.stats['files_by_extension'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            for ext, count in sorted_extensions:
                lines = self.stats['lines_by_extension'][ext]
                writer.writerow([ext, count, lines])
            
        print(f"\n💾 统计结果已导出到：{filename}")
        
    def export_markdown(self, filename: str = "project_statistics.md"):
        """导出统计结果到 Markdown 文件"""
        from datetime import datetime
            
        md_content = f"""# NecoRAG 项目统计报告\n\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n**项目路径**: {self.project_root}\n\n---\n\n## 📊 基本统计\n\n| 统计项 | 数值 |\n|--------|------|\n| 📁 总文件数 | {self.stats['total_files']:,} |\n| 📝 代码文件 | {self.stats['code_files']:,} |\n| 💾 二进制文件 | {self.stats['binary_files']:,} |\n| 📄 其他文件 | {self.stats['other_files']:,} |\n| 📂 目录数量 | {len(self.stats['directories']):,} |\n\n---\n\n## 📈 代码行数统计\n\n| 类型 | 行数 | 占比 |\n|------|------|------|\n| 总行数 | {self.stats['total_lines']:,} | 100% |\n| 代码行数 | {self.stats['code_lines']:,} | {(self.stats['code_lines'] / max(self.stats['total_lines'], 1)) * 100:.1f}% |\n| 空行数 | {self.stats['blank_lines']:,} | {(self.stats['blank_lines'] / max(self.stats['total_lines'], 1)) * 100:.1f}% |\n| 注释行数 | {self.stats['comment_lines']:,} | {(self.stats['comment_lines'] / max(self.stats['total_lines'], 1)) * 100:.1f}% |\n\n---\n\n## 📁 文件类型分布\n\n| 文件扩展名 | 文件数量 | 占比 | 行数 | 平均每文件 |\n|------------|----------|------|------|-----------|\n"""
            
        sorted_extensions = sorted(
            self.stats['files_by_extension'].items(),
            key=lambda x: x[1],
            reverse=True
        )
            
        for ext, count in sorted_extensions[:20]:  # 显示前 20 个
            lines = self.stats['lines_by_extension'][ext]
            percentage = (count / max(self.stats['total_files'], 1)) * 100
            avg_lines = lines / max(count, 1)
            md_content += f"| {ext} | {count:,} | {percentage:.1f}% | {lines:,} | {avg_lines:.1f} |\n"
            
        if len(sorted_extensions) > 20:
            remaining = len(sorted_extensions) - 20
            remaining_count = sum(count for _, count in sorted_extensions[20:])
            md_content += f"\n... 还有 {remaining} 种文件类型 ({remaining_count:,} 个文件)\n"
            
        md_content += f"\n---\n\n## 📝 代码行数分布（按文件类型）\n\n| 文件类型 | 总行数 | 占比 | 平均行数/文件 |\n|----------|--------|------|--------------|\n"
            
        sorted_lines = sorted(
            self.stats['lines_by_extension'].items(),
            key=lambda x: x[1],
            reverse=True
        )
            
        for ext, lines in sorted_lines[:15]:  # 显示前 15 个
            if lines > 0:
                percentage = (lines / max(self.stats['total_lines'], 1)) * 100
                file_count = self.stats['files_by_extension'][ext]
                avg_lines = lines / max(file_count, 1)
                md_content += f"| {ext} | {lines:,} | {percentage:.1f}% | {avg_lines:.1f} |\n"
            
        md_content += f"\n---\n\n## 📂 主要目录结构\n\n"""
            
        if self.stats['directories']:
            main_dirs = [d for d in self.stats['directories'] if '/' not in d]
            md_content += "### 一级目录\n\n"
            for dir_name in sorted(main_dirs)[:15]:
                # 统计该目录下的文件数（可选）
                md_content += f"- `{dir_name}/`\n"
                
            if len(main_dirs) > 15:
                md_content += f"\n... 还有 {len(main_dirs) - 15} 个目录\n"
                
            md_content += "\n### 子目录统计\n\n"
            sub_dirs = [d for d in self.stats['directories'] if '/' in d]
            for dir_name in sorted(sub_dirs)[:20]:
                md_content += f"- `{dir_name}/`\n"
                
            if len(sub_dirs) > 20:
                md_content += f"\n... 还有 {len(sub_dirs) - 20} 个子目录\n"
            
        md_content += f"\n---\n\n## 📊 数据质量分析\n\n"
            
        # 计算一些质量指标
        total_code_files = self.stats['code_files']
        if total_code_files > 0:
            avg_lines_per_file = self.stats['code_lines'] / total_code_files
            md_content += f"""### 代码质量指标\n\n- **平均每文件代码行数**: {avg_lines_per_file:.1f} 行\n- **代码密度**: {(self.stats['code_lines'] / max(self.stats['total_lines'], 1)) * 100:.1f}%\n- **文档化程度**: {(self.stats['comment_lines'] / max(self.stats['code_lines'], 1)) * 100:.1f}% (注释/代码)\n"""
            
        md_content += f"\n---\n\n*本报告由 NecoRAG Project Statistics 工具自动生成*\n"
            
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        print(f"📄 Markdown 报告已导出到：{filename}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='NecoRAG 项目统计工具')
    parser.add_argument(
        '-p', '--path',
        default='..',  # 默认扫描项目根目录（相对于 tools 目录）
        help='项目根目录路径 (默认：../ 即项目根目录)'
    )
    parser.add_argument(
        '-o', '--output',
        help='导出CSV文件路径'
    )
    parser.add_argument(
        '-m', '--markdown',
        help='导出 Markdown 文件路径'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='显示详细信息'
    )
    
    args = parser.parse_args()
    
    try:
        # 创建统计器并执行统计
        stats = ProjectStatistics(args.path)
        print(f"\n🎯 开始分析整个项目: {stats.project_root}")
        print("=" * 60 + "\n")
        stats.scan_project()
        stats.print_statistics()
        
        # 导出CSV（如果指定了输出文件）
        if args.output:
            stats.export_csv(args.output)
                
        # 导出 Markdown（如果指定了输出文件）
        if args.markdown:
            stats.export_markdown(args.markdown)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 统计过程中发生错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()