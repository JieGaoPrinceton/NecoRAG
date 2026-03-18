#!/usr/bin/env python3
"""
Gitee Wiki 同步工具

将项目的 REPO WIKI 同步到 Gitee wiki 页面
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import base64
import json
from typing import List, Dict, Optional
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


def check_wiki_enabled():
    """检查仓库是否启用了 Wiki"""
    url = f'{GITEE_API_BASE}/repos/{GITEE_OWNER}/{GITEE_REPO}'
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        repo_info = response.json()
        has_wiki = repo_info.get('has_wiki', False)
        print(f"仓库 Wiki 状态: {'启用' if has_wiki else '未启用'}")
        return has_wiki
    else:
        print(f"检查仓库信息失败: {response.status_code}")
        return False


def enable_wiki():
    """启用仓库 Wiki"""
    url = f'{GITEE_API_BASE}/repos/{GITEE_OWNER}/{GITEE_REPO}'
    data = {
        'wiki_enabled': True
    }
    
    response = requests.patch(url, headers=HEADERS, json=data)
    
    if response.status_code in [200, 201]:
        print("✓ Wiki 已启用")
        return True
    else:
        print(f"启用 Wiki 失败: {response.status_code}")
        print(response.json())
        return False


def get_wiki_pages():
    """获取现有的 Wiki 页面列表"""
    # 注意：Gitee 可能没有直接的 Wiki API，这里尝试几种方式
    
    # 方法1：尝试列出 wiki 页面
    url = f'{GITEE_API_BASE}/repos/{GITEE_OWNER}/{GITEE_REPO}/wikis'
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        print("Wiki API 不可用，将使用替代方案")
        return []
    else:
        print(f"获取 Wiki 页面失败: {response.status_code}")
        return []


def collect_wiki_files() -> List[Dict[str, str]]:
    """收集所有 Wiki 文件"""
    wiki_files = []
    
    if not WIKI_CONTENT_PATH.exists():
        print(f"Wiki 内容目录不存在: {WIKI_CONTENT_PATH}")
        return wiki_files
    
    # 遍历所有 .md 文件
    for md_file in WIKI_CONTENT_PATH.rglob('*.md'):
        # 获取相对路径作为页面名称
        rel_path = md_file.relative_to(WIKI_CONTENT_PATH)
        page_name = str(rel_path.with_suffix(''))
        
        # 读取文件内容
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            wiki_files.append({
                'name': page_name,
                'path': str(md_file),
                'content': content,
                'title': page_name.replace('/', ' - ')  # 简单的标题处理
            })
        except Exception as e:
            print(f"读取文件失败 {md_file}: {e}")
    
    return wiki_files


def create_or_update_wiki_page(page_info: Dict[str, str]) -> bool:
    """创建或更新 Wiki 页面"""
    # Gitee 的 Wiki API 可能不直接支持，这里使用替代方案
    # 通过创建 Issues 或使用 Git 方式来管理 Wiki
    
    page_name = page_info['name']
    content = page_info['content']
    title = page_info['title']
    
    print(f"处理页面: {page_name}")
    
    # 方案1：使用 Issues 来模拟 Wiki 页面
    # 这是最可靠的替代方案
    return create_wiki_issue(page_name, title, content)


def create_wiki_issue(page_name: str, title: str, content: str) -> bool:
    """通过创建 Issue 来模拟 Wiki 页面"""
    url = f'{GITEE_API_BASE}/repos/{GITEE_OWNER}/{GITEE_REPO}/issues'
    
    # 暂时不使用标签，避免API错误
    # labels = ['wiki', f'wiki-{page_name.replace("/", "-").lower()}']
    
    data = {
        'title': f'[Wiki] {title}',
        'body': content
        # 'labels': labels  # 暂时禁用标签
    }
    
    response = requests.post(url, headers=HEADERS, json=data)
    
    if response.status_code in [200, 201]:
        issue = response.json()
        print(f"  ✓ 创建 Issue #{issue['number']} 作为 Wiki 页面")
        return True
    else:
        print(f"  ✗ 创建 Wiki Issue 失败: {response.status_code}")
        try:
            error_info = response.json()
            print(f"    错误详情: {error_info}")
        except:
            print(f"    响应内容: {response.text[:200]}")
        return False


def sync_wiki_structure():
    """同步 Wiki 结构到 README"""
    readme_content = """# NecoRAG Wiki 导航

欢迎来到 NecoRAG Wiki！这里是项目的完整文档中心。

## 📚 文档目录

"""
    
    # 收集所有 Wiki 页面
    wiki_files = collect_wiki_files()
    
    # 按目录分组
    grouped_pages = {}
    for page in wiki_files:
        path_parts = page['name'].split('/')
        if len(path_parts) > 1:
            category = path_parts[0]
            if category not in grouped_pages:
                grouped_pages[category] = []
            grouped_pages[category].append(page)
        else:
            if 'uncategorized' not in grouped_pages:
                grouped_pages['uncategorized'] = []
            grouped_pages['uncategorized'].append(page)
    
    # 生成导航内容
    for category, pages in grouped_pages.items():
        category_title = category.replace('-', ' ').title()
        readme_content += f"\n### {category_title}\n\n"
        
        for page in sorted(pages, key=lambda x: x['name']):
            # 创建 Issue 链接格式
            issue_title = f"[Wiki] {page['title']}"
            # 这里需要实际创建后才能知道 Issue 编号
            readme_content += f"- [{page['title']}](../../issues?q=is%3Aissue+is%3Aopen+label%3Awiki+\"{issue_title}\")\n"
    
    readme_content += """

## 📖 使用说明

本 Wiki 使用 GitHub Issues 来管理文档页面。每个 Wiki 页面对应一个带有 `wiki` 标签的 Issue。

## 🔄 更新说明

Wiki 内容会定期从项目源文件同步更新。

---
*自动生成于 {}*
""".format(time.strftime('%Y-%m-%d %H:%M:%S'))
    
    return readme_content


def create_main_wiki_readme():
    """创建主 Wiki README"""
    readme_content = sync_wiki_structure()
    
    # 保存到本地
    wiki_readme_path = Path('WIKI_README.md')
    with open(wiki_readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✓ 主 Wiki README 已生成: {wiki_readme_path}")
    
    # 也上传到仓库根目录
    try:
        with open(wiki_readme_path, 'rb') as f:
            content = f.read()
        
        # 使用现有的上传函数
        from push_to_gitee import upload_file
        if upload_file('WIKI_README.md', content, 'Update Wiki navigation'):
            print("✓ 主 Wiki README 已上传到仓库")
            return True
        else:
            print("✗ 主 Wiki README 上传失败")
            return False
    except Exception as e:
        print(f"✗ 处理主 Wiki README 失败: {e}")
        return False


def sync_wiki_to_gitee():
    """同步 Wiki 到 Gitee"""
    print("=== 开始同步 Wiki 到 Gitee ===\n")
    
    # 1. 检查配置
    if not GITEE_TOKEN:
        print("错误：未找到 GITEE_TOKEN，请检查 .env 文件")
        return False
    
    # 2. 检查仓库
    print("1. 检查仓库状态...")
    from push_to_gitee import check_repo_exists, create_repo
    
    if not check_repo_exists():
        print("正在创建仓库...")
        if not create_repo():
            print("创建仓库失败")
            return False
    else:
        print("✓ 仓库已存在")
    
    # 3. 收集 Wiki 文件
    print("\n2. 收集 Wiki 文件...")
    wiki_files = collect_wiki_files()
    print(f"找到 {len(wiki_files)} 个 Wiki 页面")
    
    if not wiki_files:
        print("没有找到 Wiki 文件")
        return False
    
    # 4. 处理每个 Wiki 页面
    print("\n3. 同步 Wiki 页面...")
    success_count = 0
    fail_count = 0
    
    for i, page_info in enumerate(wiki_files, 1):
        print(f"\n[{i}/{len(wiki_files)}] {page_info['name']}")
        if create_or_update_wiki_page(page_info):
            success_count += 1
        else:
            fail_count += 1
        
        # 添加延迟避免 API 限制
        if i < len(wiki_files):
            time.sleep(1)
    
    # 5. 创建主导航页面
    print("\n4. 创建主 Wiki 导航...")
    if create_main_wiki_readme():
        print("✓ 主导航页面创建成功")
    else:
        print("✗ 主导航页面创建失败")
    
    # 6. 输出统计
    print(f"\n=== 同步完成 ===")
    print(f"成功: {success_count} 个页面")
    print(f"失败: {fail_count} 个页面")
    print(f"Wiki 地址: https://gitee.com/{GITEE_OWNER}/{GITEE_REPO}/issues?label=wiki")
    
    return fail_count == 0


def main():
    """主函数"""
    try:
        success = sync_wiki_to_gitee()
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