"""
Dashboard 使用示例
演示如何启动和使用 NecoRAG Dashboard
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from necorag.dashboard import DashboardServer, ConfigManager
from necorag.dashboard.models import RAGProfile


def example_config_manager():
    """示例：使用配置管理器"""
    print("=" * 60)
    print("配置管理器使用示例")
    print("=" * 60)
    
    # 创建配置管理器
    config_manager = ConfigManager(config_dir="./example_configs")
    
    # 创建新的配置 Profile
    print("\n1. 创建新 Profile")
    profile = config_manager.create_profile(
        profile_name="示例配置",
        description="用于演示的配置文件"
    )
    print(f"   创建成功: {profile.profile_name} (ID: {profile.profile_id})")
    
    # 更新配置参数
    print("\n2. 更新模块参数")
    config_manager.update_profile(profile.profile_id, {
        "whiskers_config": {
            "chunk_size": 1024,
            "enable_ocr": False
        },
        "retrieval_config": {
            "top_k": 20,
            "pounce_threshold": 0.90
        }
    })
    print("   更新成功")
    
    # 获取活动配置
    print("\n3. 获取活动配置")
    active_profile = config_manager.get_active_profile()
    if active_profile:
        print(f"   活动 Profile: {active_profile.profile_name}")
        print(f"   Whiskers chunk_size: {active_profile.whiskers_config.parameters['chunk_size']}")
        print(f"   Retrieval top_k: {active_profile.retrieval_config.parameters['top_k']}")
    
    # 列出所有配置
    print("\n4. 所有 Profiles:")
    all_profiles = config_manager.get_all_profiles()
    for p in all_profiles:
        status = " [活动]" if p.is_active else ""
        print(f"   - {p.profile_name}{status}")
    
    print("\n" + "=" * 60)


def example_dashboard_server():
    """示例：启动 Dashboard 服务器"""
    print("=" * 60)
    print("Dashboard 服务器启动示例")
    print("=" * 60)
    
    print("\n启动服务器...")
    print("访问地址: http://localhost:8000")
    print("API 文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止服务器\n")
    
    # 创建并启动服务器
    server = DashboardServer(
        config_dir="./example_configs",
        host="0.0.0.0",
        port=8000
    )
    
    server.run()


def example_api_usage():
    """示例：API 使用方法"""
    print("=" * 60)
    print("API 使用示例")
    print("=" * 60)
    
    print("\n以下是可用的 API 接口:\n")
    
    print("Profile 管理:")
    print("  GET    /api/profiles              - 获取所有 Profiles")
    print("  GET    /api/profiles/{id}         - 获取单个 Profile")
    print("  POST   /api/profiles              - 创建新 Profile")
    print("  PUT    /api/profiles/{id}         - 更新 Profile")
    print("  DELETE /api/profiles/{id}         - 删除 Profile")
    print("  POST   /api/profiles/{id}/activate - 激活 Profile")
    
    print("\n模块参数管理:")
    print("  GET /api/profiles/{id}/modules/{module} - 获取模块参数")
    print("  PUT /api/profiles/{id}/modules/{module} - 更新模块参数")
    
    print("\n统计信息:")
    print("  GET  /api/stats    - 获取统计信息")
    print("  POST /api/stats/reset - 重置统计信息")
    
    print("\n" + "=" * 60)


def example_profile_structure():
    """示例：Profile 结构说明"""
    print("=" * 60)
    print("Profile 结构示例")
    print("=" * 60)
    
    # 创建一个示例 Profile
    profile = RAGProfile(
        profile_id="example_001",
        profile_name="示例配置",
        description="演示 Profile 结构"
    )
    
    print("\nProfile 包含以下模块配置:\n")
    
    print("1. Whiskers Engine (感知层):")
    for key, value in profile.whiskers_config.parameters.items():
        print(f"   - {key}: {value}")
    
    print("\n2. Memory (记忆层):")
    for key, value in profile.memory_config.parameters.items():
        print(f"   - {key}: {value}")
    
    print("\n3. Retrieval (检索层):")
    for key, value in profile.retrieval_config.parameters.items():
        print(f"   - {key}: {value}")
    
    print("\n4. Grooming (巩固层):")
    for key, value in profile.grooming_config.parameters.items():
        print(f"   - {key}: {value}")
    
    print("\n5. Purr (交互层):")
    for key, value in profile.purr_config.parameters.items():
        print(f"   - {key}: {value}")
    
    print("\n" + "=" * 60)


def main():
    """主函数"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║         NecoRAG Dashboard 使用示例                      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()
    
    # 示例 1: Profile 结构
    example_profile_structure()
    
    # 示例 2: 配置管理器
    example_config_manager()
    
    # 示例 3: API 使用
    example_api_usage()
    
    # 示例 4: 启动 Dashboard
    print("\n是否启动 Dashboard 服务器？ (y/n): ", end="")
    choice = input().strip().lower()
    
    if choice == 'y':
        example_dashboard_server()
    else:
        print("\n提示: 可以运行以下命令启动 Dashboard:")
        print("  python -m necorag.dashboard.dashboard")
        print("  或")
        print("  python dashboard_demo.py")


if __name__ == "__main__":
    # 如果直接运行此脚本，默认启动 Dashboard
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        main()
    else:
        # 直接启动服务器
        example_dashboard_server()
