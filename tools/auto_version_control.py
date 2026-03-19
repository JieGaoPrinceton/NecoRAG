#!/usr/bin/env python3
"""
NecoRAG 自动版本控制系统

功能:
1. 自动检测项目变更（基于 Git）
2. 智能分析变更类型（重大重构/新功能/Bug 修复/文档更新）
3. 自动递增版本号并同步到所有文件
4. 生成更新日志

使用方法:
    python tools/auto_version_control.py           # 自动模式
    python tools/auto_version_control.py -i        # 交互模式
    python tools/auto_version_control.py --dry-run # 预览模式
    python tools/auto_version_control.py --auto    # 完全自动（无确认）
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# 导入版本管理器
sys.path.insert(0, str(Path(__file__).parent))
from version_manager import VersionManager


class AutoVersionControl:
    """自动版本控制器"""
    
    def __init__(self, root_dir: str = None):
        """初始化自动版本控制器
        
        Args:
            root_dir: 项目根目录
        """
        if root_dir is None:
            self.root_dir = Path(__file__).parent.parent
        else:
            self.root_dir = Path(root_dir)
        
        self.vm = VersionManager(self.root_dir)
        self.config_file = Path(__file__).parent / "auto_version_config.json"
        self.config = self._load_config()
        
        # 变更类型定义
        self.CHANGE_TYPES = {
            'MAJOR': ('major', '🔴 重大重构', ['BREAKING CHANGE', 'refactor!:', 'perf!:']),
            'MINOR': ('minor', '🟢 新功能', ['feat:', 'feature:', 'new:']),
            'PATCH': ('patch', '🔵 Bug 修复', ['fix:', 'bugfix:', 'hotfix:']),
            'DOCS': ('patch', '📝 文档更新', ['.md', 'docs/', 'README']),
            'CONFIG': ('patch', '⚙️ 配置调整', ['pyproject.toml', '.env', 'config']),
            'TEST': ('patch', '🧪 测试更新', ['test/', 'tests/', 'pytest']),
        }
        
        # 核心文件列表（修改这些文件触发 major 更新）
        self.CORE_FILES = [
            'src/necorag.py',
            'src/core/',
            'interface/',
            'design/design.md',
        ]
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 默认配置
        return {
            'auto_mode': False,
            'interactive': False,
            'dry_run': False,
            'commit_changes': True,
            'generate_changelog': True,
            'exclude_patterns': ['*.log', '*.tmp', '.git/', '__pycache__/'],
            'core_files': self.CORE_FILES,
        }
    
    def detect_changes(self) -> Dict[str, List[str]]:
        """检测项目变更
        
        Returns:
            变更文件字典，按类型分组
        """
        changes = {
            'added': [],
            'modified': [],
            'deleted': [],
        }
        
        try:
            # 获取 Git 状态
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if not line.strip():
                    continue
                
                status = line[:2].strip()
                file_path = line[3:].strip()
                
                # 跳过排除的文件
                if self._should_exclude(file_path):
                    continue
                
                if status.startswith('A'):
                    changes['added'].append(file_path)
                elif status.startswith('M'):
                    changes['modified'].append(file_path)
                elif status.startswith('D'):
                    changes['deleted'].append(file_path)
            
            # 如果没有变更，检查最近的 commit
            if not any(changes.values()):
                print("ℹ️  检测到未提交的变更，分析最近的 commit...")
                recent_commits = self._get_recent_commits(limit=5)
                for commit in recent_commits:
                    if 'feat:' in commit.lower():
                        changes['modified'].append('src/features/')
                    elif 'fix:' in commit.lower():
                        changes['modified'].append('src/bugs/')
        
        except subprocess.CalledProcessError as e:
            print(f"⚠️  警告：无法获取 Git 状态：{e}")
            # 如果不是 git 仓库，返回空变更
            if not (self.root_dir / '.git').exists():
                print("ℹ️  当前目录不是 Git 仓库，跳过变更检测")
                return changes
        
        return changes
    
    def _should_exclude(self, file_path: str) -> bool:
        """判断文件是否应该被排除"""
        exclude_patterns = self.config.get('exclude_patterns', [])
        for pattern in exclude_patterns:
            if pattern in file_path:
                return True
        return False
    
    def _get_recent_commits(self, limit: int = 5) -> List[str]:
        """获取最近的 commit 信息"""
        try:
            result = subprocess.run(
                ['git', 'log', f'-{limit}', '--pretty=%s'],
                cwd=self.root_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split('\n')
        except subprocess.CalledProcessError:
            return []
    
    def analyze_change_type(self, changes: Dict[str, List[str]]) -> Tuple[str, str]:
        """分析变更类型
        
        Args:
            changes: 变更文件字典
            
        Returns:
            (递增级别，变更描述)
        """
        change_reasons = []
        highest_priority = 'PATCH'
        
        # 检查新增文件
        for file_path in changes.get('added', []):
            if 'src/' in file_path and file_path.endswith('.py'):
                if self._is_higher_priority('MINOR', highest_priority):
                    highest_priority = 'MINOR'
                change_reasons.append(f"新增模块：{file_path}")
        
        # 检查修改文件
        for file_path in changes.get('modified', []):
            # 检查是否为核心文件
            for core_file in self.CORE_FILES:
                if core_file in file_path:
                    if self._is_higher_priority('MAJOR', highest_priority):
                        highest_priority = 'MAJOR'
                    change_reasons.append(f"核心架构修改：{file_path}")
                    break
            
            # 检查是否为文档
            if file_path.endswith('.md'):
                if self._is_higher_priority('DOCS', highest_priority):
                    highest_priority = 'DOCS'
                change_reasons.append(f"文档更新：{file_path}")
            
            # 检查配置文件
            elif file_path in ['pyproject.toml', '.env', 'requirements.txt']:
                if self._is_higher_priority('CONFIG', highest_priority):
                    highest_priority = 'CONFIG'
                change_reasons.append(f"配置调整：{file_path}")
            
            # 检查测试文件
            elif 'test' in file_path.lower():
                if self._is_higher_priority('TEST', highest_priority):
                    highest_priority = 'TEST'
                change_reasons.append(f"测试更新：{file_path}")
        
        # 优先级顺序：MAJOR > MINOR > PATCH
        priority_order = {'MAJOR': 3, 'MINOR': 2, 'PATCH': 1}
        
        level_key = highest_priority
        bump_level, level_desc, _ = self.CHANGE_TYPES[level_key]
        
        # 生成变更描述
        change_summary = f"{level_desc} ({len(change_reasons)} 个文件)"
        
        return bump_level, change_summary
    
    def _is_higher_priority(self, new_level: str, current_level: str) -> bool:
        """判断新版本级别是否更高"""
        priority_order = {'MAJOR': 3, 'MINOR': 2, 'PATCH': 1}
        return priority_order.get(new_level, 0) > priority_order.get(current_level, 0)
    
    def run(self, interactive: bool = False, dry_run: bool = False, auto: bool = False):
        """执行自动版本控制
        
        Args:
            interactive: 是否交互式确认
            dry_run: 是否预览模式
            auto: 是否完全自动模式
        """
        print("\n" + "="*60)
        print("NecoRAG 自动版本控制系统")
        print("="*60 + "\n")
        
        # 1. 检测变更
        print("🔍 检测项目变更...")
        changes = self.detect_changes()
        
        total_changes = sum(len(v) for v in changes.values())
        if total_changes == 0:
            print("✅ 未检测到变更，无需更新版本")
            return
        
        print(f"检测到 {total_changes} 个文件变更:")
        for change_type, files in changes.items():
            if files:
                emoji = {'added': '➕', 'modified': '✏️', 'deleted': '❌'}[change_type]
                print(f"  {emoji} {change_type}: {len(files)} 个文件")
        
        # 2. 分析变更类型
        print("\n📊 分析变更类型...")
        bump_level, change_summary = self.analyze_change_type(changes)
        print(f"变更类型：{change_summary}")
        
        # 3. 获取当前版本
        current_version = self.vm.read_version()
        print(f"当前版本：{current_version}")
        
        # 4. 计算新版本
        new_version = self._calculate_new_version(current_version, bump_level)
        print(f"建议更新：{bump_level} → {new_version}")
        
        # 5. 用户确认（交互模式）
        if interactive and not auto:
            confirmed = self._confirm_update(bump_level, new_version, change_summary)
            if not confirmed:
                print("❌ 已取消版本更新")
                return
        
        # 6. 执行更新
        if dry_run:
            print(f"\n📝 预览模式：将更新版本号为 {new_version}")
        else:
            print(f"\n⚙️  执行版本更新...")
            
            # 设置新版本
            self.vm.set_version(new_version)
            
            # 同步到所有文件
            self.vm.sync(dry_run=False)
            
            # 生成更新日志
            if self.config.get('generate_changelog', True):
                self._update_changelog(new_version, change_summary, changes)
            
            print(f"\n✅ 版本已更新为：{new_version}")
        
        print("="*60 + "\n")
    
    def _calculate_new_version(self, current_version: str, bump_level: str) -> str:
        """计算新版本号
        
        Args:
            current_version: 当前版本号
            bump_level: 递增级别
            
        Returns:
            新的版本号
        """
        import re
        
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(-[a-zA-Z]+)?$', current_version)
        if not match:
            raise ValueError(f"无效的版本号：{current_version}")
        
        major = int(match.group(1))
        minor = int(match.group(2))
        patch = int(match.group(3))
        suffix = match.group(4) or ''
        
        if bump_level == 'major':
            major += 1
            minor = 0
            patch = 0
        elif bump_level == 'minor':
            minor += 1
            patch = 0
        elif bump_level == 'patch':
            patch += 1
        
        return f"{major}.{minor}.{patch}{suffix}"
    
    def _confirm_update(self, bump_level: str, new_version: str, change_summary: str) -> bool:
        """用户确认更新
        
        Returns:
            是否确认更新
        """
        print("\n请确认版本更新:")
        print(f"  递增级别：{bump_level}")
        print(f"  新版本：{new_version}")
        print(f"  变更摘要：{change_summary}")
        print("\n选项:")
        print("  1) 确认更新 ✓")
        print("  2) 选择其他级别")
        print("  3) 跳过本次更新 ✗")
        
        choice = input("\n请选择 [1-3]: ").strip()
        
        if choice == '1':
            return True
        elif choice == '2':
            print("\n选择递增级别:")
            print("  1) patch (小更新)")
            print("  2) minor (新功能)")
            print("  3) major (重大变更)")
            
            level_choice = input("请选择 [1-3]: ").strip()
            level_map = {'1': 'patch', '2': 'minor', '3': 'major'}
            return level_map.get(level_choice, 'patch')
        else:
            return False
    
    def _update_changelog(self, new_version: str, change_summary: str, changes: Dict):
        """更新 CHANGELOG.md
        
        Args:
            new_version: 新版本号
            change_summary: 变更摘要
            changes: 变更文件字典
        """
        changelog_path = self.root_dir / "CHANGELOG.md"
        
        # 如果不存在，创建基本的 CHANGELOG
        if not changelog_path.exists():
            changelog_path.write_text("# 更新日志\n\n", encoding='utf-8')
        
        # 读取现有内容
        content = changelog_path.read_text(encoding='utf-8')
        
        # 生成新的更新条目
        date_str = datetime.now().strftime("%Y-%m-%d")
        entry = f"""## [{new_version}] - {date_str}

### {change_summary}

#### 变更详情
"""
        
        # 添加文件变更列表
        for change_type, files in changes.items():
            if files:
                type_name = {'added': '新增', 'modified': '修改', 'deleted': '删除'}[change_type]
                entry += f"\n**{type_name}文件**:\n"
                for file in files[:5]:  # 最多显示 5 个
                    entry += f"- `{file}`\n"
                if len(files) > 5:
                    entry += f"- ... 等共 {len(files)} 个文件\n"
        
        entry += "\n---\n\n"
        
        # 插入到开头
        new_content = content.replace("# 更新日志\n\n", "# 更新日志\n\n" + entry)
        
        # 写回文件
        changelog_path.write_text(new_content, encoding='utf-8')
        print(f"✓ 已更新更新日志：{changelog_path}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='NecoRAG 自动版本控制系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s              # 自动模式（推荐）
  %(prog)s -i           # 交互模式（需要确认）
  %(prog)s --dry-run    # 预览模式（不实际更新）
  %(prog)s --auto       # 完全自动（无确认）
        """
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='交互模式，需要用户确认'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不实际写入文件'
    )
    
    parser.add_argument(
        '--auto',
        action='store_true',
        help='完全自动模式，无需确认'
    )
    
    args = parser.parse_args()
    
    # 创建自动版本控制器
    avc = AutoVersionControl()
    
    try:
        # 执行自动版本控制
        avc.run(
            interactive=args.interactive,
            dry_run=args.dry_run,
            auto=args.auto
        )
    
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
