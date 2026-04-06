"""
监控仪表板
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta
import json
from fastapi import FastAPI, APIRouter
from fastapi.responses import HTMLResponse

from .metrics import system_metrics, app_metrics
from .health import health_checker
from .alerts import alert_manager
from .config import get_monitoring_config


class MonitoringDashboard:
    """监控仪表板"""
    
    def __init__(self):
        self.app = FastAPI(title="NecoRAG Monitoring Dashboard")
        self.router = APIRouter(prefix="/api/v1/monitoring")
        self.config = get_monitoring_config()
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        
        @self.router.get("/metrics/system")
        async def get_system_metrics():
            """获取系统指标"""
            metrics = system_metrics.collect_system_metrics()
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": metrics
            }
        
        @self.router.get("/metrics/application")
        async def get_application_metrics():
            """获取应用指标"""
            # 这里应该返回应用特定的指标
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "rag_response_time_avg": 1.2,
                    "api_requests_per_second": 45.6,
                    "cache_hit_rate": 87.3
                }
            }
        
        @self.router.get("/health")
        async def get_health_status():
            """获取健康状态"""
            results = await health_checker.run_all_checks()
            report = health_checker.get_health_report()
            return report
        
        @self.router.get("/alerts")
        async def get_alerts(active_only: bool = True):
            """获取告警信息"""
            if active_only:
                alerts = alert_manager.get_active_alerts()
            else:
                alerts = alert_manager.get_alert_history(hours=24)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "alerts": [
                    {
                        "id": alert.id,
                        "rule_name": alert.rule_name,
                        "level": alert.level.value,
                        "status": alert.status.value,
                        "summary": alert.summary,
                        "start_time": alert.start_time.isoformat(),
                        "end_time": alert.end_time.isoformat() if alert.end_time else None
                    }
                    for alert in alerts
                ]
            }
        
        @self.router.get("/dashboard")
        async def get_dashboard_data():
            """获取仪表板汇总数据"""
            # 并发获取各项数据
            import asyncio
            
            system_task = asyncio.create_task(self._get_system_overview())
            health_task = asyncio.create_task(self._get_health_overview())
            alerts_task = asyncio.create_task(self._get_alerts_overview())
            
            system_data, health_data, alerts_data = await asyncio.gather(
                system_task, health_task, alerts_task
            )
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "system": system_data,
                "health": health_data,
                "alerts": alerts_data
            }
        
        # 将路由添加到应用
        self.app.include_router(self.router)
        
        # 添加静态页面路由
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_page():
            """监控仪表板页面"""
            return self._get_dashboard_html()
    
    async def _get_system_overview(self) -> Dict[str, Any]:
        """获取系统概览"""
        metrics = system_metrics.collect_system_metrics()
        
        return {
            "cpu_usage": round(metrics.get("cpu_usage_percent", 0), 1),
            "memory_usage": round(metrics.get("memory_usage_percent", 0), 1),
            "disk_usage": round(metrics.get("disk_usage_percent", 0), 1),
            "uptime_hours": round(metrics.get("uptime_seconds", 0) / 3600, 1)
        }
    
    async def _get_health_overview(self) -> Dict[str, Any]:
        """获取健康概览"""
        report = health_checker.get_health_report()
        return {
            "status": report["status"],
            "total_checks": report["summary"]["total"],
            "healthy_checks": report["summary"]["healthy"],
            "problem_checks": report["summary"]["unhealthy"] + report["summary"]["degraded"]
        }
    
    async def _get_alerts_overview(self) -> Dict[str, Any]:
        """获取告警概览"""
        active_alerts = alert_manager.get_active_alerts()
        
        # 按级别统计
        level_counts = {}
        for alert in active_alerts:
            level = alert.level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            "active_alerts": len(active_alerts),
            "by_level": level_counts,
            "critical_alerts": level_counts.get("critical", 0)
        }
    
    def _get_dashboard_html(self) -> str:
        """获取仪表板 HTML 页面"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>NecoRAG 监控仪表板</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; text-align: center; }
        .metric-label { text-align: center; color: #666; margin-top: 10px; }
        .status-indicator { width: 15px; height: 15px; border-radius: 50%; display: inline-block; margin-right: 10px; }
        .healthy { background-color: #4CAF50; }
        .degraded { background-color: #FF9800; }
        .unhealthy { background-color: #F44336; }
        .unknown { background-color: #9E9E9E; }
        .chart-container { height: 200px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 NecoRAG 监控仪表板</h1>
            <p>实时系统监控和健康状态</p>
        </div>
        
        <div class="dashboard-grid">
            <div class="card">
                <h3>系统状态</h3>
                <div id="system-status" class="metric-value">加载中...</div>
                <div class="metric-label">整体健康状况</div>
            </div>
            
            <div class="card">
                <h3>CPU 使用率</h3>
                <div id="cpu-usage" class="metric-value">0%</div>
                <div class="metric-label">处理器负载</div>
            </div>
            
            <div class="card">
                <h3>内存使用率</h3>
                <div id="memory-usage" class="metric-value">0%</div>
                <div class="metric-label">RAM 使用情况</div>
            </div>
            
            <div class="card">
                <h3>活跃告警</h3>
                <div id="active-alerts" class="metric-value">0</div>
                <div class="metric-label">需要关注的问题</div>
            </div>
        </div>
        
        <div class="card" style="margin-top: 20px;">
            <h3>实时指标图表</h3>
            <div class="chart-container">
                <canvas id="metrics-chart"></canvas>
            </div>
        </div>
    </div>

    <script>
        // 定期刷新数据
        setInterval(updateDashboard, 5000);
        updateDashboard();
        
        async function updateDashboard() {
            try {
                const response = await fetch('/api/v1/monitoring/dashboard');
                const data = await response.json();
                
                // 更新系统状态
                const statusElement = document.getElementById('system-status');
                const statusClass = data.health.status;
                statusElement.innerHTML = `<span class="status-indicator ${statusClass}"></span>${statusClass.toUpperCase()}`;
                
                // 更新指标
                document.getElementById('cpu-usage').textContent = data.system.cpu_usage + '%';
                document.getElementById('memory-usage').textContent = data.system.memory_usage + '%';
                document.getElementById('active-alerts').textContent = data.alerts.active_alerts;
                
            } catch (error) {
                console.error('更新仪表板失败:', error);
            }
        }
    </script>
</body>
</html>
        """


# 全局仪表板实例
monitoring_dashboard = MonitoringDashboard()


def get_monitoring_app() -> FastAPI:
    """获取监控应用实例"""
    return monitoring_dashboard.app