#!/usr/bin/env python3
"""
NecoRAG 双仓库同步工具
功能：同步代码到 Gitee 和 GitHub
"""

import subprocess
import sys
from pathlib import Path


class Colors:
    """颜色定义"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


def print_header(text: str):
    """打印标题"""
    print(f"{Colors.BLUE}╔{'═' * 50}╗{Colors.NC}")
    print(f"{Colors.BLUE}║   {text:<46} ║{Colors.NC}")
    print(f"{Colors.BLUE}╚{'═' * 50}╝{Colors.NC}")


def print_success(text: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")


def print_error(text: str):
    """打印错误信息"""
    print(f"{Colors.RED}❌ {text}{Colors.NC}")


def print_warning(text: str):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.NC}")


def print_info(text: str):
    """打印信息"""
    print(f"{Colors.BLUE}📍 {text}{Colors.NC}")


def run_command(cmd: list, check: bool = True) -> tuple:
    """运行命令"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout or "", e.stderr or ""


def get_current_branch() -> str:
    """获取当前分支"""
    success, stdout, stderr = run_command(["git", "branch", "--show-current"])
    if success:
        return stdout.strip()
    return "main"


def check_git_status() -> bool:
    """检查 Git 状态"""
    success, stdout, stderr = run_command(["git", "status", "--short"], check=False)
    if not success:
        return False
    
    if stdout.strip():
        print_warning("有以下未提交的更改:")
        for line in stdout.strip().split('\n'):
            print(f"  {line}")
        return True
    return True


def get_remotes() -> dict:
    """获取远程仓库配置"""
    success, stdout, stderr = run_command(["git", "remote", "-v"])
    if not success:
        return {}
    
    remotes = {}
    for line in stdout.strip().split('\n'):
        if line:
            parts = line.split()
            if len(parts) >= 2:
                name = parts[0]
                url = parts[1]
                if name not in remotes:
                    remotes[name] = url
    
    return remotes


def push_to_remote(remote: str, branch: str) -> bool:
    """推送到远程仓库"""
    print(f"\n{Colors.YELLOW}🚀 推送到 {remote}...{Colors.NC}")
    print(f"{Colors.BLUE}{'─' * 50}{Colors.NC}")
    
    success, stdout, stderr = run_command(["git", "push", remote, branch], check=False)
    
    if success:
        print_success(f"{remote} 推送成功!")
        return True
    else:
        print_error(f"{remote} 推送失败!")
        if stderr:
            print(f"{Colors.RED}{stderr}{Colors.NC}")
        return False


def show_status():
    """显示当前状态"""
    print(f"\n{Colors.YELLOW}📊 当前状态{Colors.NC}")
    print(f"{Colors.BLUE}{'─' * 50}{Colors.NC}")
    
    # 远程仓库配置
    print(f"\n{Colors.YELLOW}远程仓库配置:{Colors.NC}")
    remotes = get_remotes()
    for name, url in remotes.items():
        if name in ['origin', 'github']:
            print(f"  {name}: {url}")
    
    # 最近提交记录
    print(f"\n{Colors.YELLOW}最近提交记录:{Colors.NC}")
    success, stdout, stderr = run_command(["git", "log", "--oneline", "-5"])
    if success:
        for line in stdout.strip().split('\n'):
            print(f"  {line}")
    
    # 分支信息
    print(f"\n{Colors.YELLOW}分支信息:{Colors.NC}")
    success, stdout, stderr = run_command(["git", "branch", "-a"])
    if success:
        for line in stdout.strip().split('\n'):
            print(f"  {line}")


def sync_all(branch: str):
    """同步到所有仓库"""
    print(f"\n{Colors.GREEN}🚀 开始同步到两个仓库...{Colors.NC}")
    print(f"{Colors.BLUE}{'─' * 50}{Colors.NC}")
    
    # 推送到 Gitee
    gitee_success = push_to_remote("origin", branch)
    
    if not gitee_success:
        print_error("Gitee 推送失败，终止同步")
        return False
    
    print()
    
    # 推送到 GitHub
    github_success = push_to_remote("github", branch)
    
    if not github_success:
        print_warning("GitHub 推送失败，请检查 Token 配置或网络连接")
        print_info("Gitee 已成功更新")
        return False
    
    print()
    print_header("✅ 同步完成！两个仓库都已更新")
    print()
    print_info("Gitee 仓库：https://gitee.com/qijie2026/NecoRAG")
    print_info("GitHub 仓库：https://github.com/JieGaoPrinceton/NecoRAG")
    
    return True


def main():
    """主函数"""
    print_header("NecoRAG 双仓库同步工具")
    print()
    
    # 获取当前分支
    branch = get_current_branch()
    print_info(f"当前分支：{branch}")
    
    # 检查 Git 状态
    if not check_git_status():
        print_error("Git 状态检查失败")
        return 1
    
    # 获取远程仓库
    remotes = get_remotes()
    if 'origin' not in remotes:
        print_error("未配置 Gitee 远程仓库 (origin)")
        return 1
    
    if 'github' not in remotes:
        print_error("未配置 GitHub 远程仓库 (github)")
        print_info("添加命令：git remote add github https://github.com/JieGaoPrinceton/NecoRAG.git")
        return 1
    
    # 菜单选择
    print()
    print(f"{Colors.YELLOW}请选择同步方式:{Colors.NC}")
    print("  1) 仅推送到 Gitee (origin)")
    print("  2) 仅推送到 GitHub (github)")
    print("  3) 同时推送到两个仓库 (推荐)")
    print("  4) 只查看状态，不推送")
    print()
    
    choice = input("请输入选项 (1/2/3/4): ").strip()
    
    if choice == '1':
        # 仅推送到 Gitee
        success = push_to_remote("origin", branch)
        if success:
            print_info("Gitee 仓库：https://gitee.com/qijie2026/NecoRAG")
        
    elif choice == '2':
        # 仅推送到 GitHub
        success = push_to_remote("github", branch)
        if success:
            print_info("GitHub 仓库：https://github.com/JieGaoPrinceton/NecoRAG")
        
    elif choice == '3':
        # 同时推送
        sync_all(branch)
        
    elif choice == '4':
        # 查看状态
        show_status()
        
    else:
        print_error("无效的选项")
        return 1
    
    print()
    print_success("操作完成！")
    return 0


if __name__ == "__main__":
    sys.exit(main())
