#!/usr/bin/env python3
"""
NecoRAG 版本管理工具

功能:
1. 读取和显示当前版本号
2. 更新版本号 (自动递增)
3. 批量更新项目中所有 Markdown 文件的版本号引用
4. 同步版本号到 pyproject.toml

使用方法:
    python tools/version_manager.py show          # 显示当前版本
    python tools/version_manager.py bump major    # 主版本号 +1 (1.9.0 -> 2.0.0)
    python tools/version_manager.py bump minor    # 次版本号 +1 (1.9.0 -> 1.10.0)
    python tools/version_manager.py bump patch    # 补丁号 +1 (1.9.0 -> 1.9.1)
    python tools/version_manager.py set 1.10.0    # 直接设置版本号
    python tools/version_manager.py sync          # 同步版本号到所有文件
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime


class VersionManager:
    """版本管理器"""
    
    def __init__(self, root_dir: str = None):
        """初始化版本管理器
        
        Args:
            root_dir: 项目根目录，默认为脚本所在项目的根目录
        """
        if root_dir is None:
            self.root_dir = Path(__file__).parent.parent
        else:
            self.root_dir = Path(root_dir)
        
        self.version_file = self.root_dir / "VERSION"
        self.pyproject_file = self.root_dir / "pyproject.toml"
    
    def read_version(self) -> str:
        """读取当前版本号
        
        Returns:
            版本号字符串
        """
        if not self.version_file.exists():
            raise FileNotFoundError(f"VERSION 文件不存在：{self.version_file}")
        
        with open(self.version_file, 'r', encoding='utf-8') as f:
            version = f.read().strip()
        
        return version
    
    def write_version(self, version: str):
        """写入版本号
        
        Args:
            version: 新的版本号
        """
        # 验证版本号格式
        if not re.match(r'^\d+\.\d+\.\d+(-[a-zA-Z]+)?$', version):
            raise ValueError(
                f"无效的版本号格式：{version}\n"
                "正确格式示例：1.9.0, 1.9.0-alpha, 2.0.0-beta"
            )
        
        # 写入 VERSION 文件
        with open(self.version_file, 'w', encoding='utf-8') as f:
            f.write(f"{version}\n")
        
        print(f"✓ 已更新 VERSION 文件：{version}")
    
    def bump_version(self, level: str = 'patch') -> str:
        """递增版本号
        
        Args:
            level: 递增级别 ('major', 'minor', 'patch')
        
        Returns:
            新的版本号
        """
        current = self.read_version()
        
        # 解析版本号
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(-[a-zA-Z]+)?$', current)
        if not match:
            raise ValueError(f"无法解析的版本号：{current}")
        
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        suffix = match.group(4) or ''
        
        # 递增版本号
        if level == 'major':
            major += 1
            minor = 0
            patch = 0
        elif level == 'minor':
            minor += 1
            patch = 0
        elif level == 'patch':
            patch += 1
        else:
            raise ValueError(f"无效的递增级别：{level}，必须是 'major', 'minor' 或 'patch'")
        
        new_version = f"{major}.{minor}.{patch}{suffix}"
        self.write_version(new_version)
        
        return new_version
    
    def set_version(self, version: str):
        """直接设置版本号
        
        Args:
            version: 新的版本号
        """
        self.write_version(version)
    
    def update_pyproject(self, version: str = None):
        """更新 pyproject.toml 中的版本号
        
        Args:
            version: 版本号，如果不指定则使用当前版本号
        """
        if version is None:
            version = self.read_version()
        
        if not self.pyproject_file.exists():
            print(f"⚠ 警告：pyproject.toml 不存在，跳过更新")
            return
        
        with open(self.pyproject_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换 version 行
        old_pattern = r'^version\s*=\s*"[^"]*"'
        new_line = f'version = "{version}"'
        
        new_content = re.sub(old_pattern, new_line, content, flags=re.MULTILINE)
        
        if content == new_content:
            print(f"⚠ pyproject.toml 中的版本号已经是 {version}")
        else:
            with open(self.pyproject_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ 已更新 pyproject.toml: {version}")
    
    def find_md_files(self) -> list:
        """查找项目中所有的 Markdown 文件
        
        Returns:
            Markdown 文件路径列表
        """
        md_files = []
        
        # 排除的目录
        exclude_dirs = {
            '.git', '__pycache__', 'node_modules', 
            '.pytest_cache', '.mypy_cache', 'venv', 
            'env', '.venv', 'dist', 'build'
        }
        
        for root, dirs, files in os.walk(self.root_dir):
            # 移除排除的目录
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.md'):
                    file_path = Path(root) / file
                    md_files.append(file_path)
        
        return md_files
    
    def update_md_files(self, version: str = None, dry_run: bool = False):
        """更新所有 Markdown 文件中的版本号
        
        Args:
            version: 新的版本号，如果不指定则使用当前版本号
            dry_run: 如果为 True，只显示将要进行的更改而不实际写入
        """
        if version is None:
            version = self.read_version()
        
        # 提取版本信息
        version_match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version)
        if not version_match:
            raise ValueError(f"无效的版本号：{version}")
        
        major, minor, patch = version_match.groups()
        short_version = f"{major}.{minor}"  # 例如：1.9
        
        # 查找所有 Markdown 文件
        md_files = self.find_md_files()
        print(f"找到 {len(md_files)} 个 Markdown 文件")
        
        # 需要更新的模式（按优先级顺序）
        patterns = [
            # 1. 先处理徽章链接中的版本号（避免重复）
            (r'(version-|badge/)(v?\d+\.\d+\.\d+(?:-[a-zA-Z]+)?)', r'\g<1>' + f'{version}'),
            
            # 2. v1.8.0-alpha, v1.9.0-alpha 等（完整版本号）
            (r'(?<![.\d])v(\d+\.\d+\.\d+(?:-[a-zA-Z]+)?)(?![.\d])', f'v{version}'),
            
            # 3. V1.8.0, V1.9.0 等（大写版本号的完整形式）
            (r'(?<![.\d])V(\d+\.\d+\.\d+)(?![.\d])', f'V{version}'),
            
            # 4. 短版本号 v1.8, v1.9 等（确保不匹配完整版本号）
            (r'(?<![.\d])v(\d+\.\d+)(?![-.\d])', f'v{short_version}'),
            
            # 5. 纯文本版本号（单独出现，前后无字母或数字）
            (r'(?<![a-zA-Z.\d])(\d+\.\d+\.\d+(?:-[a-zA-Z]+)?)(?![a-zA-Z.\d])', version),
            
            # 6. 更新日期
            (r'\*\*最后更新\*\*:\s*\d{4}-\d{2}-\d{2}', 
             f'**最后更新**: {datetime.now().strftime("%Y-%m-%d")}'),
        ]
        
        updated_count = 0
        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                new_content = original_content
                
                # 应用所有替换模式
                for pattern, replacement in patterns:
                    new_content = re.sub(pattern, replacement, new_content)
                
                # 如果内容有变化，写入文件
                if new_content != original_content:
                    if not dry_run:
                        with open(md_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"✓ 更新：{md_file.relative_to(self.root_dir)}")
                        updated_count += 1
                    else:
                        print(f"📝 将要更新：{md_file.relative_to(self.root_dir)}")
                
            except Exception as e:
                print(f"✗ 处理失败 {md_file}: {e}")
        
        # 显示统计
        print(f"\n{'='*60}")
        if dry_run:
            print(f"预览模式：将有 {updated_count} 个文件被更新")
        else:
            print(f"完成！已更新 {updated_count}/{len(md_files)} 个文件")
            print(f"当前版本号：{version}")
    
    def sync(self, dry_run: bool = False):
        """同步版本号到所有相关文件
        
        Args:
            dry_run: 如果为 True，只显示将要进行的更改而不实际写入
        """
        version = self.read_version()
        
        print(f"当前版本号：{version}")
        print(f"{'='*60}")
        
        # 更新 pyproject.toml
        if not dry_run:
            self.update_pyproject(version)
        else:
            print(f"📝 将要更新 pyproject.toml: {version}")
        
        # 更新所有 Markdown 文件
        self.update_md_files(version, dry_run)
    
    def show_info(self):
        """显示版本信息"""
        version = self.read_version()
        
        print(f"\n{'='*60}")
        print(f"NecoRAG 版本信息")
        print(f"{'='*60}")
        print(f"当前版本：{version}")
        
        # 解析版本号
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(-[a-zA-Z]+)?$', version)
        if match:
            major, minor, patch, suffix = match.groups()
            print(f"\n版本组成:")
            print(f"  主版本号 (Major): {major}")
            print(f"  次版本号 (Minor): {minor}")
            print(f"  补丁号 (Patch):   {patch}")
            if suffix:
                print(f"  预发布标识：      {suffix}")
        
        # 统计文件
        md_files = self.find_md_files()
        print(f"\n项目统计:")
        print(f"  Markdown 文件数：{len(md_files)}")
        print(f"  VERSION 文件：   {self.version_file}")
        print(f"  pyproject 文件： {self.pyproject_file}")
        print(f"{'='*60}\n")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='NecoRAG 版本管理工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s show                    # 显示当前版本
  %(prog)s bump major              # 主版本号 +1
  %(prog)s bump minor              # 次版本号 +1
  %(prog)s bump patch              # 补丁号 +1
  %(prog)s set 1.10.0              # 直接设置为 1.10.0
  %(prog)s sync                    # 同步版本到所有文件
  %(prog)s sync --dry-run          # 预览同步操作
        """
    )
    
    parser.add_argument(
        'command',
        choices=['show', 'bump', 'set', 'sync'],
        help='命令类型'
    )
    
    parser.add_argument(
        'value',
        nargs='?',
        default=None,
        help='命令参数 (版本号或递增级别)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不实际写入文件'
    )
    
    args = parser.parse_args()
    
    # 创建版本管理器
    vm = VersionManager()
    
    try:
        if args.command == 'show':
            vm.show_info()
        
        elif args.command == 'bump':
            if not args.value:
                args.value = 'patch'  # 默认递增补丁号
            
            new_version = vm.bump_version(args.value)
            print(f"✓ 版本号已递增：{new_version}")
            
            # 自动同步到其他文件
            if not args.dry_run:
                vm.sync()
        
        elif args.command == 'set':
            if not args.value:
                print("✗ 错误：set 命令必须指定版本号")
                print("示例：python version_manager.py set 1.10.0")
                sys.exit(1)
            
            vm.set_version(args.value)
            print(f"✓ 版本号已设置为：{args.value}")
            
            # 自动同步到其他文件
            if not args.dry_run:
                vm.sync()
        
        elif args.command == 'sync':
            vm.sync(dry_run=args.dry_run)
    
    except Exception as e:
        print(f"✗ 错误：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
