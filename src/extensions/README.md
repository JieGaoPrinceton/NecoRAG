# NecoRAG 监控告警模块

## 概述

监控告警模块为 NecoRAG 系统提供全面的监控解决方案，包括系统指标收集、健康检查、告警管理和可视化仪表板。

## 功能特性

### 📊 指标收集
- **系统级指标**：CPU、内存、磁盘、网络使用率
- **应用级指标**：RAG 响应时间、API 调用统计、缓存命中率
- **Python 运行时**：垃圾回收、内存使用、进程信息
- **Prometheus 格式**：标准指标导出格式

### 🩺 健康检查
- **多维度检查**：数据库、Redis、LLM 服务、磁盘空间
- **并发执行**：高效的并行健康检查
- **历史记录**：检查结果历史追踪
- **灵活配置**：可自定义检查项和阈值

### ⚠️ 告警管理
- **智能告警**：基于指标阈值和健康状态的告警
- **多级告警**：INFO、WARNING、ERROR、CRITICAL 四级告警
- **多种通知**：控制台、邮件、Webhook、Slack 通知
- **告警抑制**：避免重复告警和告警风暴

### 📈 可视化仪表板
- **实时监控**：系统状态和指标的实时展示
- **交互式界面**：Web 界面查看监控数据
- **API 接口**：RESTful API 获取监控信息
- **响应式设计**：适配不同设备屏幕

## 快速开始

### 1. 安装依赖

```bash
pip install psutil apscheduler aiohttp
```

### 2. 环境变量配置

```bash
# 监控配置
export MONITORING_METRICS_ENABLED=true
export MONITORING_METRICS_PORT=9090
export MONITORING_COLLECTION_INTERVAL=15

export MONITORING_HEALTH_CHECK_ENABLED=true
export MONITORING_HEALTH_CHECK_INTERVAL=30

export MONITORING_ALERTS_ENABLED=true
export MONITORING_ALERT_EVALUATION_INTERVAL=60

# 通知配置
export MONITORING_NOTIFICATION_CHANNELS=console,email,slack
export MONITORING_EMAIL_SMTP_SERVER=smtp.gmail.com
export MONITORING_EMAIL_SMTP_PORT=587
export MONITORING_EMAIL_USERNAME=your-email@gmail.com
export MONITORING_EMAIL_PASSWORD=your-app-password
export MONITORING_EMAIL_RECIPIENTS=admin@company.com

export MONITORING_SLACK_WEBHOOKS=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### 3. 基本使用

```python
from src.monitoring import (
    monitoring_service,
    system_metrics,
    health_checker,
    alert_manager
)

# 启动监控服务
await monitoring_service.start()

# 手动收集指标
metrics = system_metrics.collect_system_metrics()
print(f"CPU 使用率: {metrics['cpu_usage_percent']}%")

# 执行健康检查
results = await health_checker.run_all_checks()
for result in results:
    print(f"{result.name}: {result.status.value}")

# 评估告警规则
alerts = await alert_manager.evaluate_rules(metrics_data=metrics)
```

## 核心组件

### 指标收集 (metrics.py)

```python
# 系统指标收集
system_data = system_metrics.collect_system_metrics()
print(f"内存使用: {system_data['memory_usage_percent']}%")

# 应用指标记录
app_metrics.record_rag_response_time(1.5, success=True)
app_metrics.record_api_call("/api/search", 200, 0.8)

# Prometheus 导出
prometheus_data = system_metrics.export_prometheus_format()
```

### 健康检查 (health.py)

```python
# 注册自定义健康检查
async def check_custom_service():
    # 实现你的检查逻辑
    return {
        "status": HealthStatus.HEALTHY,
        "message": "服务正常",
        "details": {"response_time": 100}
    }

health_checker.register_check("custom_service", check_custom_service)

# 获取健康报告
report = health_checker.get_health_report()
print(f"整体状态: {report['status']}")
```

### 告警管理 (alerts.py)

```python
# 创建自定义告警规则
rule = AlertRule(
    name="high_error_rate",
    expression="api_error_rate > 10",
    level=AlertLevel.ERROR,
    description="API 错误率过高"
)
alert_manager.add_alert_rule(rule)

# 评估告警
alerts = await alert_manager.evaluate_rules(
    metrics_data={"api_error_rate": 15.5}
)
```

## Web 仪表板

### 启动监控服务

```python
from src.monitoring import create_monitoring_app
import uvicorn

app = create_monitoring_app()
uvicorn.run(app, host="0.0.0.0", port=9090)
```

### 访问仪表板

```
http://localhost:9090/          # 仪表板界面
http://localhost:9090/api/v1/monitoring/dashboard  # API 数据
http://localhost:9090/api/v1/monitoring/metrics/system  # 系统指标
http://localhost:9090/api/v1/monitoring/health  # 健康状态
```

## 高级配置

### 自定义指标收集

```python
from src.monitoring.metrics import MetricType

# 记录自定义指标
system_metrics.record_metric(
    "custom_business_metric",
    value=42.5,
    metric_type=MetricType.GAUGE,
    labels={"environment": "production", "region": "us-east"}
)
```

### 扩展健康检查

```python
# 添加数据库连接检查
async def check_database():
    try:
        # 实际的数据库连接检查
        connection_ok = await db.ping()
        return {
            "status": HealthStatus.HEALTHY if connection_ok else HealthStatus.UNHEALTHY,
            "message": "数据库连接正常" if connection_ok else "数据库连接失败"
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "message": f"数据库检查异常: {str(e)}"
        }

health_checker.register_check("database", check_database, critical=True)
```

### 配置告警通知

```python
from src.monitoring.alerts import WebhookNotification

# 添加自定义 Webhook 通知
webhook_channel = WebhookNotification("https://your-webhook-url.com")
alert_manager.add_notification_channel(webhook_channel)
```

## 性能优化

### 指标采样策略

```python
# 高频指标 - 每秒采样
system_metrics.record_metric("api_requests", 1, labels={"endpoint": "/search"})

# 低频指标 - 每分钟采样
system_metrics.record_metric("daily_active_users", user_count)
```

### 健康检查超时控制

```python
# 设置检查超时
async def slow_check_with_timeout():
    try:
        result = await asyncio.wait_for(actual_check(), timeout=5.0)
        return result
    except asyncio.TimeoutError:
        return {
            "status": HealthStatus.DEGRADED,
            "message": "检查超时"
        }
```

## 监控最佳实践

### 1. 分层监控策略

```python
# 基础设施层监控
infrastructure_checks = ["cpu", "memory", "disk", "network"]

# 服务层监控  
service_checks = ["database", "redis", "llm_service"]

# 应用层监控
application_checks = ["api_response_time", "error_rate", "business_metrics"]
```

### 2. 告警分级处理

```python
# Critical - 立即处理
critical_rules = [
    AlertRule("system_down", "health_status == UNHEALTHY", AlertLevel.CRITICAL),
    AlertRule("high_cpu", "cpu_usage > 95", AlertLevel.CRITICAL)
]

# Warning - 关注但非紧急
warning_rules = [
    AlertRule("moderate_cpu", "cpu_usage > 80", AlertLevel.WARNING),
    AlertRule("low_memory", "memory_usage > 85", AlertLevel.WARNING)
]
```

### 3. 通知渠道选择

```python
# 生产环境 - 多渠道通知
production_channels = ["email", "slack", "webhook"]

# 开发环境 - 控制台通知为主
development_channels = ["console", "email"]

# 测试环境 - 最小通知
testing_channels = ["console"]
```

## 故障排除

### 常见问题

1. **指标收集失败**
   ```bash
   # 检查 psutil 权限
   pip install --upgrade psutil
   ```

2. **健康检查超时**
   ```python
   # 调整超时配置
   config.health_check_timeout = 30
   ```

3. **告警重复发送**
   ```python
   # 检查告警去重逻辑
   alert_manager._evaluate_expression.cache_clear()
   ```

### 日志配置

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 监控模块专用日志
monitoring_logger = logging.getLogger('monitoring')
monitoring_logger.setLevel(logging.DEBUG)
```

## 集成示例

### 与 FastAPI 集成

```python
from fastapi import FastAPI
from src.monitoring import create_monitoring_app

# 主应用
app = FastAPI()

# 挂载监控应用
app.mount("/monitoring", create_monitoring_app())

# 在主应用中记录指标
@app.middleware("http")
async def metrics_middleware(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    app_metrics.record_api_call(
        str(request.url.path),
        response.status_code,
        duration
    )
    
    return response
```

### 与现有系统集成

```python
# 在系统启动时初始化监控
async def startup_event():
    await monitoring_service.start()
    
    # 注册应用特定的健康检查
    health_checker.register_check("rag_engine", check_rag_engine)

# 在系统关闭时清理
async def shutdown_event():
    await monitoring_service.stop()
```

## API 参考

完整的 API 文档可通过 Swagger UI 访问监控服务的 `/docs` 端点。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进监控模块！