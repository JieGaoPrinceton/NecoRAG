#!/usr/bin/env python3
"""
简化版 Wiki 同步工具

将 Wiki 内容整理并上传到仓库的 docs 目录
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import base64
from typing import List, Dict
import time

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

# Wiki 配置
WIKI_BASE_PATH = Path('.qoder/repowiki/zh')
WIKI_CONTENT_PATH = WIKI_BASE_PATH / 'content'
DOCS_TARGET_PATH = 'docs/wiki'


def check_repo_exists():
    """检查仓库是否存在"""
    url = f'{GITEE_API_BASE}/repos/{GITEE_OWNER}/{GITEE_REPO}'
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        print(f"✓ 仓库 {GITEE_OWNER}/{GITEE_REPO} 存在")
        return True
    else:
        print(f"✗ 仓库检查失败: {response.status_code}")
        return False


def collect_wiki_files() -> List[Dict[str, str]]:
    """收集所有 Wiki 文件"""
    wiki_files = []
    
    if not WIKI_CONTENT_PATH.exists():
        print(f"Wiki 内容目录不存在: {WIKI_CONTENT_PATH}")
        return wiki_files
    
    # 遍历所有 .md 文件
    for md_file in WIKI_CONTENT_PATH.rglob('*.md'):
        # 获取相对路径
        rel_path = md_file.relative_to(WIKI_CONTENT_PATH)
        target_path = f"{DOCS_TARGET_PATH}/{rel_path}"
        
        # 读取文件内容
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            wiki_files.append({
                'source_path': str(md_file),
                'target_path': str(target_path),
                'content': content,
                'name': str(rel_path.with_suffix('')),
                'title': rel_path.stem
            })
        except Exception as e:
            print(f"读取文件失败 {md_file}: {e}")
    
    return wiki_files


def upload_file_to_gitee(file_path: str, content: str, message: str = "Upload wiki file") -> bool:
    """上传文件到 Gitee"""
    # Gitee API 要求 base64 编码
    content_base64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    
    url = f'{GITEE_API_BASE}/repos/{GITEE_OWNER}/{GITEE_REPO}/contents/{file_path}'
    
    data = {
        'content': content_base64,
        'message': message,
        'branch': 'main',
    }
    
    try:
        # 先检查文件是否已存在
        check_response = requests.get(url, headers=HEADERS, timeout=10)
        
        if check_response.status_code == 200:
            # 文件存在，更新它
            check_data = check_response.json()
            # 处理可能返回列表的情况
            if isinstance(check_data, list) and len(check_data) > 0:
                sha = check_data[0].get('sha')
            elif isinstance(check_data, dict):
                sha = check_data.get('sha')
            else:
                sha = None
            
            if sha:
                data['sha'] = sha
                response = requests.put(url, headers=HEADERS, json=data, timeout=10)
            else:
                # SHA获取失败，当作新文件处理
                response = requests.post(url, headers=HEADERS, json=data, timeout=10)
        else:
            # 文件不存在，创建它
            response = requests.post(url, headers=HEADERS, json=data, timeout=10)
        
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"  上传失败: {response.status_code}")
            try:
                error_msg = response.json()
                print(f"  错误详情: {error_msg}")
            except:
                print(f"  响应内容: {response.text[:100]}")
            return False
            
    except Exception as e:
        print(f"  上传异常: {str(e)}")
        return False


def create_wiki_navigation(wiki_files: List[Dict[str, str]]) -> str:
    """创建 Wiki 导航页面"""
    nav_content = """# NecoRAG Wiki 文档中心

欢迎来到 NecoRAG Wiki 文档中心！这里包含了项目的完整技术文档。

## 📚 文档目录

"""
    
    # 按目录分组
    grouped_files = {}
    root_files = []
    
    for file_info in wiki_files:
        path_parts = file_info['name'].split('/')
        if len(path_parts) == 1:
            root_files.append(file_info)
        else:
            category = path_parts[0]
            if category not in grouped_files:
                grouped_files[category] = []
            grouped_files[category].append(file_info)
    
    # 添加根目录文件
    if root_files:
        nav_content += "### 通用文档\n\n"
        for file_info in sorted(root_files, key=lambda x: x['name']):
            nav_content += f"- [{file_info['title']}]({file_info['target_path']})\n"
        nav_content += "\n"
    
    # 添加分组文件
    for category, files in sorted(grouped_files.items()):
        category_title = category.replace('-', ' ').title()
        nav_content += f"### {category_title}\n\n"
        
        for file_info in sorted(files, key=lambda x: x['name']):
            # 移除前缀目录名
            display_name = '/'.join(file_info['name'].split('/')[1:])
            if not display_name:
                display_name = file_info['title']
            nav_content += f"- [{display_name}]({file_info['target_path']})\n"
        nav_content += "\n"
    
    nav_content += f"""
## 📖 使用说明

本文档集合包含了 NecoRAG 项目的完整技术文档，涵盖了：

- 系统架构设计
- 核心模块实现
- 部署配置指南
- 开发测试文档

## 🔄 更新说明

文档会随着项目发展持续更新和完善。

---
*文档生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
*项目地址: https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}*
"""
    
    return nav_content


def sync_wiki_to_docs():
    """同步 Wiki 到 docs 目录"""
    print("=== 开始同步 Wiki 到 docs 目录 ===\n")
    
    # 1. 检查配置
    if not GITEE_TOKEN:
        print("错误：未找到 GITEE_TOKEN，请检查 .env 文件")
        return False
    
    # 2. 检查仓库
    print("1. 检查仓库...")
    if not check_repo_exists():
        return False
    
    # 3. 收集 Wiki 文件
    print("\n2. 收集 Wiki 文件...")
    wiki_files = collect_wiki_files()
    print(f"找到 {len(wiki_files)} 个 Wiki 文件")
    
    if not wiki_files:
        print("没有找到 Wiki 文件")
        return False
    
    # 4. 上传所有 Wiki 文件
    print("\n3. 上传 Wiki 文件...")
    success_count = 0
    fail_count = 0
    
    for i, file_info in enumerate(wiki_files, 1):
        print(f"[{i}/{len(wiki_files)}] 上传 {file_info['name']}")
        if upload_file_to_gitee(
            file_info['target_path'], 
            file_info['content'],
            f"Upload wiki: {file_info['name']}"
        ):
            success_count += 1
            print(f"  ✓ 上传成功")
        else:
            fail_count += 1
            print(f"  ✗ 上传失败")
        
        # 添加延迟避免 API 限制
        if i < len(wiki_files):
            time.sleep(0.5)
    
    # 5. 创建导航页面
    print("\n4. 创建导航页面...")
    nav_content = create_wiki_navigation(wiki_files)
    nav_path = f"{DOCS_TARGET_PATH}/README.md"
    
    if upload_file_to_gitee(nav_path, nav_content, "Create wiki navigation"):
        print("✓ 导航页面创建成功")
        success_count += 1
    else:
        print("✗ 导航页面创建失败")
        fail_count += 1
    
    # 6. 输出统计
    print(f"\n=== 同步完成 ===")
    print(f"成功: {success_count} 个文件")
    print(f"失败: {fail_count} 个文件")
    print(f"文档地址: https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}/tree/main/docs/wiki")
    print(f"导航页面: https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}/blob/main/docs/wiki/README.md")
    
    return fail_count == 0


def main():
    """主函数"""
    try:
        success = sync_wiki_to_docs()
        if success:
            print("\n✓ Wiki 同步成功!")
            sys.exit(0)
        else:
            print("\n✗ Wiki 同步失败!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()