"""
创建 Gitee 仓库并推送代码
"""
import requests
import json
import subprocess
import os
import sys

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Gitee API 配置
ACCESS_TOKEN = "9559fb0386f79f9b7507c03ca408413e"
REPO_NAME = "NecoRAG"
REPO_DESCRIPTION = "NecoRAG - Neuro-Cognitive Retrieval-Augmented Generation Framework"

def create_gitee_repo():
    """创建 Gitee 仓库"""
    print("正在创建 Gitee 仓库...")
    
    url = "https://gitee.com/api/v5/user/repos"
    
    data = {
        "access_token": ACCESS_TOKEN,
        "name": REPO_NAME,
        "description": REPO_DESCRIPTION,
        "private": False,
        "has_issues": True,
        "has_wiki": True
    }
    
    try:
        response = requests.post(url, data=data)
        
        if response.status_code == 201:
            result = response.json()
            print(f"[OK] 仓库创建成功！")
            print(f"   仓库地址: {result['html_url']}")
            print(f"   SSH 地址: {result['ssh_url']}")
            print(f"   HTTPS 地址: {result['clone_url']}")
            return result
        elif response.status_code == 422:
            print("[INFO] 仓库已存在，继续推送代码...")
            return {"html_url": f"https://gitee.com/qijie2026/{REPO_NAME}"}
        else:
            print(f"[ERROR] 创建仓库失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"[ERROR] 创建仓库异常: {e}")
        return None

def push_to_gitee():
    """推送代码到 Gitee"""
    print("\n正在推送代码到 Gitee...")
    
    # Gitee 远程仓库地址
    gitee_url = f"https://qijie2026:{ACCESS_TOKEN}@gitee.com/qijie2026/{REPO_NAME}.git"
    
    commit_msg = """Initial commit: NecoRAG v1.0.0-alpha
    
- Five-layer cognitive architecture
- Dashboard configuration management
- Complete documentation and examples"""
    
    commands = [
        ["git", "add", "."],
        ["git", "commit", "-m", commit_msg],
        ["git", "branch", "-M", "main"],
        ["git", "remote", "add", "origin", gitee_url],
        ["git", "push", "-u", "origin", "main"]
    ]
    
    for cmd in commands:
        try:
            print(f"   执行: {' '.join(cmd[:2])}...")
            result = subprocess.run(
                cmd,
                cwd="d:/code/NecoRAG",
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode != 0:
                # 如果 remote 已存在，先删除再添加
                if "remote origin already exists" in result.stderr:
                    print("   远程仓库已存在，更新地址...")
                    subprocess.run(
                        ["git", "remote", "set-url", "origin", gitee_url],
                        cwd="d:/code/NecoRAG",
                        capture_output=True
                    )
                    # 重新推送
                    subprocess.run(
                        ["git", "push", "-u", "origin", "main"],
                        cwd="d:/code/NecoRAG",
                        capture_output=True,
                        text=True,
                        encoding='utf-8',
                        errors='ignore'
                    )
                else:
                    print(f"   [WARN] 命令返回非零: {result.stderr}")
        except Exception as e:
            print(f"   [ERROR] 执行失败: {e}")
    
    print("[OK] 代码推送完成！")

def main():
    print("="*60)
    print("  NecoRAG - Gitee 仓库创建和代码推送")
    print("="*60)
    print()
    
    # 创建仓库
    repo_info = create_gitee_repo()
    
    if repo_info or True:  # 即使仓库已存在也继续
        # 推送代码
        push_to_gitee()
        
        print()
        print("="*60)
        print("[SUCCESS] 完成！")
        print("="*60)
        print(f"仓库地址: https://gitee.com/qijie2026/{REPO_NAME}")
        print()

if __name__ == "__main__":
    # 检查 requests 库
    try:
        import requests
    except ImportError:
        print("正在安装 requests 库...")
        subprocess.run(["pip", "install", "requests", "-q"])
        import requests
    
    main()
