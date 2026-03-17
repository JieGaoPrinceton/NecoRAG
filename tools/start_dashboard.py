#!/usr/bin/env python3
"""
NecoRAG Dashboard 启动脚本
快速启动 Web 管理界面
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.dashboard import DashboardServer


def main():
    """启动 Dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="NecoRAG Dashboard - 配置管理和监控界面"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="服务器主机地址 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="服务器端口 (默认: 8000)"
    )
    parser.add_argument(
        "--config-dir",
        type=str,
        default="./configs",
        help="配置文件存储目录 (默认: ./configs)"
    )
    
    args = parser.parse_args()
    
    # 创建并启动服务器
    server = DashboardServer(
        config_dir=args.config_dir,
        host=args.host,
        port=args.port
    )
    
    server.run()


if __name__ == "__main__":
    main()
