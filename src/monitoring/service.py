"""
监控服务主入口
整合所有监控功能，提供统一的服务接口
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from .config import get_monitoring_config
from .metrics import system_metrics, app_metrics
from .health import health_checker
from .alerts import alert_manager
from .dashboard import monitoring_dashboard


class MonitoringService:
    """监控服务主类"""
    
    def __init__(self):
        self.config = get_monitoring_config()
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        
        # 初始化各个组件
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化监控组件"""
        # 可以在这里添加组件初始化逻辑
        pass
    
    async def start(self):
        """启动监控服务"""
        if self.is_running:
            self.logger.warning("监控服务已在运行")
            return
        
        self.logger.info("正在启动监控服务...")
        
        try:
            # 启动调度器
            self.scheduler.start()
            
            # 添加定时任务
            if self.config.metrics_enabled:
                self.scheduler.add_job(
                    self._collect_metrics,
                    'interval',
                    seconds=self.config.collection_interval,
                    id='metrics_collection'
                )
            
            if self.config.health_check_enabled:
                self.scheduler.add_job(
                    self._perform_health_checks,
                    'interval',
                    seconds=self.config.health_check_interval,
                    id='health_checks'
                )
            
            if self.config.alerts_enabled:
                self.scheduler.add_job(
                    self._evaluate_alerts,
                    'interval',
                    seconds=self.config.alert_evaluation_interval,
                    id='alert_evaluation'
                )
            
            self.is_running = True
            self.logger.info("监控服务启动成功")
            
        except Exception as e:
            self.logger.error(f"监控服务启动失败: {str(e)}")
            raise
    
    async def stop(self):
        """停止监控服务"""
        if not self.is_running:
            self.logger.warning("监控服务未在运行")
            return
        
        self.logger.info("正在停止监控服务...")
        
        try:
            # 关闭调度器
            self.scheduler.shutdown()
            self.is_running = False
            self.logger.info("监控服务已停止")
            
        except Exception as e:
            self.logger.error(f"停止监控服务时出错: {str(e)}")
    
    async def _collect_metrics(self):
        """收集指标数据"""
        try:
            # 收集系统指标
            system_metrics.collect_system_metrics()
            
            # 记录一些关键指标
            system_data = system_metrics.collect_system_metrics()
            system_metrics.record_metric(
                "cpu_usage_percent", 
                system_data.get("cpu_usage_percent", 0)
            )
            system_metrics.record_metric(
                "memory_usage_percent",
                system_data.get("memory_usage_percent", 0)
            )
            
            self.logger.debug("指标收集完成")
            
        except Exception as e:
            self.logger.error(f"指标收集失败: {str(e)}")
    
    async def _perform_health_checks(self):
        """执行健康检查"""
        try:
            results = await health_checker.run_all_checks()
            overall_status = health_checker.get_overall_status(results)
            
            if overall_status != "healthy":
                self.logger.warning(f"系统健康状态: {overall_status}")
            
            self.logger.debug(f"健康检查完成，状态: {overall_status}")
            
        except Exception as e:
            self.logger.error(f"健康检查执行失败: {str(e)}")
    
    async def _evaluate_alerts(self):
        """评估告警规则"""
        try:
            # 获取最新数据
            system_data = system_metrics.collect_system_metrics()
            health_report = health_checker.get_health_report()
            health_status = health_report.get("status", "unknown")
            
            # 评估告警
            alerts = await alert_manager.evaluate_rules(
                metrics_data=system_data,
                health_status=health_status
            )
            
            if alerts:
                self.logger.info(f"触发了 {len(alerts)} 个告警")
            
        except Exception as e:
            self.logger.error(f"告警评估失败: {str(e)}")
    
    def get_status(self) -> dict:
        """获取服务状态"""
        return {
            "running": self.is_running,
            "config": {
                "metrics_enabled": self.config.metrics_enabled,
                "health_check_enabled": self.config.health_check_enabled,
                "alerts_enabled": self.config.alerts_enabled
            },
            "components": {
                "metrics_collector": "active" if self.config.metrics_enabled else "disabled",
                "health_checker": "active" if self.config.health_check_enabled else "disabled",
                "alert_manager": "active" if self.config.alerts_enabled else "disabled"
            },
            "last_updated": datetime.utcnow().isoformat()
        }


# 全局监控服务实例
monitoring_service = MonitoringService()


# FastAPI 应用集成
def create_monitoring_app() -> FastAPI:
    """创建监控应用"""
    app = FastAPI(title="NecoRAG Monitoring Service")
    
    # 包含仪表板路由
    app.mount("/", monitoring_dashboard.app)
    
    @app.on_event("startup")
    async def startup_event():
        """应用启动事件"""
        await monitoring_service.start()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """应用关闭事件"""
        await monitoring_service.stop()
    
    @app.get("/status")
    async def get_service_status():
        """获取服务状态"""
        return monitoring_service.get_status()
    
    return app


# 便捷函数
async def start_monitoring():
    """启动监控服务"""
    await monitoring_service.start()

async def stop_monitoring():
    """停止监控服务"""
    await monitoring_service.stop()

def get_monitoring_status() -> dict:
    """获取监控状态"""
    return monitoring_service.get_status()