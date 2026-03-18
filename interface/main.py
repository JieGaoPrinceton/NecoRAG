"""
Interface服务主入口
同时启动RESTful API和WebSocket服务
"""

import asyncio
import logging
from typing import Optional

from .api import create_api_app, run_api_server
from .websocket import websocket_manager


class InterfaceService:
    """接口服务主类"""
    
    def __init__(self, api_port: int = 8000, ws_port: int = 8001):
        self.api_port = api_port
        self.ws_port = ws_port
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    async def start_services(self):
        """启动所有服务"""
        self.logger.info("正在启动Interface服务...")
        
        try:
            # 创建API应用
            api_app = create_api_app()
            
            # 启动WebSocket服务器
            ws_task = asyncio.create_task(
                websocket_manager.start_server(port=self.ws_port)
            )
            
            # 启动API服务器
            from uvicorn import Server, Config
            config = Config(
                api_app,
                host="0.0.0.0",
                port=self.api_port,
                log_level="info"
            )
            api_server = Server(config)
            
            self.logger.info(f"✓ RESTful API服务启动于 http://0.0.0.0:{self.api_port}")
            self.logger.info(f"✓ WebSocket服务启动于 ws://0.0.0.0:{self.ws_port}")
            self.logger.info("✓ Interface服务启动完成")
            
            # 运行API服务器
            await api_server.serve()
            
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，正在停止服务...")
        except Exception as e:
            self.logger.error(f"服务启动失败: {str(e)}")
            raise
        finally:
            await self.stop_services()
    
    async def stop_services(self):
        """停止所有服务"""
        self.logger.info("正在停止Interface服务...")
        # 这里可以添加清理逻辑
        self.logger.info("服务已停止")


def run_interface_service(api_port: int = 8000, ws_port: int = 8001):
    """运行接口服务"""
    service = InterfaceService(api_port, ws_port)
    asyncio.run(service.start_services())


if __name__ == "__main__":
    run_interface_service()