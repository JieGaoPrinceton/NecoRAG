"""
Dashboard 启动脚本
快速启动 NecoRAG Dashboard
"""

import argparse
from necorag.dashboard.server import DashboardServer


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="NecoRAG Dashboard")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="主机地址")
    parser.add_argument("--port", type=int, default=8000, help="端口号")
    parser.add_argument("--config-dir", type=str, default="./configs", help="配置目录")
    
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
