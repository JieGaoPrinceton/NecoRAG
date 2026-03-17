#!/usr/bin/env python3
"""
Gitee 项目推送工具

使用 Gitee API 将项目推送到 gitee.com/qijie2026/necorag
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import base64

# 加载环境变量
load_dotenv()

# Gitee 配置
GITEE_TOKEN = os.getenv('GITEE_TOKEN')
GITEE_OWNER = os.getenv('GITEE_OWNER', 'qijie2026')
GITEE_REPO = os.getenv('GITEE_REPO', 'necorag')
GITEE_API_BASE = os.getenv('GITEE_API_BASE', 'https://gitee.com/api/v5')

# 请求头
HEADERS = {
    'Authorization': f'token {GITEE_TOKEN}',
    'Content-Type': 'application/json',
}


def check_repo_exists():
    """检查仓库是否存在"""
    # 尝试多种可能的 API 路径
    urls = [
        f'{GITEE_API_BASE}/repos/{GITEE_OWNER}/{GITEE_REPO}',
        f'{GITEE_API_BASE}/user/repos/{GITEE_OWNER}/{GITEE_REPO}',
    ]
    
    for url in urls:
        response = requests.get(url, headers=HEADERS)
        
        if response.status_code == 200:
            print(f"✓ 仓库 {GITEE_OWNER}/{GITEE_REPO} 已存在")
            return True
        elif response.status_code == 404:
            continue
        else:
            print(f"检查仓库失败：{response.status_code} - {response.json().get('message', 'Unknown error')}")
            return False
    
    print(f"✗ 仓库 {GITEE_OWNER}/{GITEE_REPO} 不存在")
    return False


def create_repo():
    """创建新仓库"""
    url = f'{GITEE_API_BASE}/user/repos'
    data = {
        'name': GITEE_REPO,
        'description': 'NecoRAG - Neuro-Cognitive Retrieval-Augmented Generation Framework',
        'homepage': 'https://github.com/NecoRAG/core',
        'private': False,
        'issue_enabled': True,
        'wiki_enabled': True,
        'pull_requests_enabled': True,
    }
    
    response = requests.post(url, headers=HEADERS, json=data)
    
    if response.status_code in [200, 201]:
        print(f"✓ 仓库 {GITEE_OWNER}/{GITEE_REPO} 创建成功")
        return True
    elif response.status_code == 422:
        error_msg = response.json().get('error', {})
        if 'base' in error_msg and '已存在' in str(error_msg.get('base', [])):
            print(f"! 仓库 {GITEE_OWNER}/{GITEE_REPO} 已存在，将直接推送文件")
            return True
        else:
            print(f"创建仓库失败：{response.status_code}")
            print(response.json())
            return False
    else:
        print(f"创建仓库失败：{response.status_code}")
        print(response.json())
        return False


def get_file_list(base_path: str = '.', exclude_dirs: list = None):
    """获取项目文件列表"""
    if exclude_dirs is None:
        exclude_dirs = ['.git', '__pycache__', '.venv', 'venv', 'env', '.idea', '.vscode', 
                       'build', 'dist', '*.egg-info', '.pytest_cache', '.tox']
    
    files = []
    base = Path(base_path)
    
    for path in base.rglob('*'):
        # 跳过排除的目录
        skip = False
        for exclude in exclude_dirs:
            if exclude in str(path):
                skip = True
                break
        
        if skip or not path.is_file():
            continue
        
        # 获取相对路径
        rel_path = path.relative_to(base)
        files.append(str(rel_path))
    
    return files


def upload_file(file_path: str, content: bytes, message: str = "Upload file", max_retries: int = 3):
    """上传单个文件到 Gitee"""
    # Gitee API 要求 base64 编码
    content_base64 = base64.b64encode(content).decode('utf-8')
    
    # Gitee 正确的 API 路径
    url = f'{GITEE_API_BASE}/repos/{GITEE_OWNER}/{GITEE_REPO}/contents/{file_path}'
    
    data = {
        'content': content_base64,
        'message': message,
        'branch': 'main',
    }
    
    for attempt in range(max_retries):
        try:
            # 先检查文件是否已存在
            check_response = requests.get(url, headers=HEADERS, timeout=10)
            
            if check_response.status_code == 200:
                check_data = check_response.json()
                # Gitee 可能返回 list（空目录）或 dict（文件存在）
                if isinstance(check_data, list):
                    # 空列表表示目录不存在，直接创建
                    response = requests.post(url, headers=HEADERS, json=data, timeout=10)
                elif isinstance(check_data, dict):
                    # 文件存在，更新它
                    sha = check_data.get('sha')
                    data['sha'] = sha
                    response = requests.put(url, headers=HEADERS, json=data, timeout=10)
                else:
                    print(f"  未知响应类型：{type(check_data)}")
                    return False
            else:
                # 文件不存在，创建它
                response = requests.post(url, headers=HEADERS, json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                return True
            
            # 记录错误
            try:
                error_data = response.json()
                if isinstance(error_data, dict):
                    error_msg = error_data.get('message', str(error_data))
                elif isinstance(error_data, list) and len(error_data) > 0:
                    error_msg = str(error_data[0]) if isinstance(error_data[0], str) else str(error_data)
                else:
                    error_msg = str(error_data)
            except:
                error_msg = response.text[:100] if response.text else 'Empty response'
            
            # 500 错误可能是暂时的，重试
            if response.status_code == 500 and attempt < max_retries - 1:
                import time
                time.sleep(1)
                continue
            
            print(f"  错误：{response.status_code} - {error_msg}")
            # 如果是认证问题或永久错误，直接返回失败
            if response.status_code in [401, 403, 404]:
                return False
                
        except Exception as e:
            if attempt < max_retries - 1:
                import time
                time.sleep(1)
                continue
            print(f"  异常：{str(e)}")
            return False
    
    return False


def push_project():
    """推送整个项目到 Gitee"""
    print("\n=== 开始推送项目到 Gitee ===\n")
    
    # 1. 检查或创建仓库
    if not check_repo_exists():
        print("正在创建仓库...")
        if not create_repo():
            print("创建仓库失败，终止推送")
            return False
    else:
        print("✓ 使用现有仓库")
    
    # 2. 获取文件列表
    print("\n正在扫描项目文件...")
    files = get_file_list()
    print(f"找到 {len(files)} 个文件")
    
    # 3. 上传文件
    success_count = 0
    fail_count = 0
    
    for i, file_path in enumerate(files, 1):
        try:
            # 读取文件内容
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # 上传文件
            if upload_file(file_path, content, f"Upload {file_path}"):
                success_count += 1
                print(f"[{i}/{len(files)}] ✓ {file_path}")
            else:
                fail_count += 1
                print(f"[{i}/{len(files)}] ✗ {file_path}")
                
        except Exception as e:
            fail_count += 1
            print(f"[{i}/{len(files)}] ✗ {file_path} - 错误：{str(e)}")
    
    # 4. 统计结果
    print(f"\n=== 推送完成 ===")
    print(f"成功：{success_count} 个文件")
    print(f"失败：{fail_count} 个文件")
    print(f"仓库地址：https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}")
    
    return fail_count == 0


def main():
    """主函数"""
    # 验证 token
    if not GITEE_TOKEN:
        print("错误：未找到 GITEE_TOKEN，请检查 .env 文件")
        sys.exit(1)
    
    # 执行推送
    success = push_project()
    
    if success:
        print("\n✓ 项目推送成功!")
        sys.exit(0)
    else:
        print("\n✗ 项目推送失败!")
        sys.exit(1)


if __name__ == '__main__':
    main()
