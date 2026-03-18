"""
告警管理系统
"""

from typing import Dict, List, Any, Callable, Optional
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .config import AlertLevel, get_monitoring_config
from .health import HealthStatus


class AlertState(Enum):
    """告警状态"""
    FIRING = "firing"      # 触发中
    RESOLVED = "resolved"  # 已解决
    SILENCED = "silenced"  # 已静默


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    expression: str
    level: AlertLevel
    description: str
    duration: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    enabled: bool = True
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """告警实例"""
    id: str
    rule_name: str
    level: AlertLevel
    summary: str
    description: str
    status: AlertState
    start_time: datetime
    end_time: Optional[datetime] = None
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    fingerprint: str = ""


class NotificationChannel:
    """通知渠道基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
    
    async def send_notification(self, alert: Alert) -> bool:
        """发送通知"""
        raise NotImplementedError


class ConsoleNotification(NotificationChannel):
    """控制台通知"""
    
    def __init__(self):
        super().__init__("console")
        self.logger = logging.getLogger(__name__)
    
    async def send_notification(self, alert: Alert) -> bool:
        try:
            message = f"[{alert.level.value.upper()}] {alert.summary}\n{alert.description}"
            if alert.status == AlertState.FIRING:
                self.logger.warning(f"🚨 告警触发: {message}")
            else:
                self.logger.info(f"✅ 告警恢复: {message}")
            return True
        except Exception as e:
            self.logger.error(f"控制台通知发送失败: {str(e)}")
            return False


class EmailNotification(NotificationChannel):
    """邮件通知"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, 
                 recipients: List[str]):
        super().__init__("email")
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.recipients = recipients
        self.logger = logging.getLogger(__name__)
    
    async def send_notification(self, alert: Alert) -> bool:
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = f"[{alert.level.value.upper()}] {alert.summary}"
            
            body = f"""
            告警详情:
            ==========
            级别: {alert.level.value}
            状态: {alert.status.value}
            时间: {alert.start_time}
            描述: {alert.description}
            
            标签: {alert.labels}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            self.logger.info(f"邮件通知已发送至 {self.recipients}")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件通知发送失败: {str(e)}")
            return False


class WebhookNotification(NotificationChannel):
    """Webhook 通知"""
    
    def __init__(self, url: str):
        super().__init__(f"webhook_{url}")
        self.url = url
        self.logger = logging.getLogger(__name__)
    
    async def send_notification(self, alert: Alert) -> bool:
        try:
            import aiohttp
            
            payload = {
                "alert_id": alert.id,
                "rule_name": alert.rule_name,
                "level": alert.level.value,
                "status": alert.status.value,
                "summary": alert.summary,
                "description": alert.description,
                "start_time": alert.start_time.isoformat(),
                "labels": alert.labels,
                "annotations": alert.annotations
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Webhook 通知发送成功: {self.url}")
                        return True
                    else:
                        self.logger.error(f"Webhook 通知发送失败: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Webhook 通知发送失败: {str(e)}")
            return False


class SlackNotification(NotificationChannel):
    """Slack 通知"""
    
    def __init__(self, webhook_url: str):
        super().__init__(f"slack_{webhook_url[-10:]}")  # 只显示 URL 后10位
        self.webhook_url = webhook_url
        self.logger = logging.getLogger(__name__)
    
    async def send_notification(self, alert: Alert) -> bool:
        try:
            import aiohttp
            
            # 根据告警级别选择颜色
            color_map = {
                AlertLevel.INFO: "#439FE0",
                AlertLevel.WARNING: "#FFA500", 
                AlertLevel.ERROR: "#E01E5A",
                AlertLevel.CRITICAL: "#FF0000"
            }
            
            payload = {
                "attachments": [{
                    "color": color_map.get(alert.level, "#439FE0"),
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"🚨 [{alert.level.value.upper()}] {alert.summary}"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": alert.description
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"*时间:* {alert.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
                                }
                            ]
                        }
                    ]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 200:
                        self.logger.info("Slack 通知发送成功")
                        return True
                    else:
                        self.logger.error(f"Slack 通知发送失败: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Slack 通知发送失败: {str(e)}")
            return False


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.config = get_monitoring_config()
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化默认通知渠道
        self._setup_default_channels()
    
    def _setup_default_channels(self):
        """设置默认通知渠道"""
        # 控制台通知（总是启用）
        self.add_notification_channel(ConsoleNotification())
        
        # 根据配置添加其他渠道
        if "email" in self.config.notification_channels and self.config.email_config:
            email_config = self.config.email_config
            email_channel = EmailNotification(
                smtp_server=email_config.get("smtp_server", ""),
                smtp_port=int(email_config.get("smtp_port", "587")),
                username=email_config.get("username", ""),
                password=email_config.get("password", ""),
                recipients=email_config.get("recipients", "").split(",")
            )
            self.add_notification_channel(email_channel)
        
        # Webhook 通知
        for url in self.config.webhook_urls:
            self.add_notification_channel(WebhookNotification(url))
        
        # Slack 通知
        for webhook_url in self.config.slack_webhooks:
            self.add_notification_channel(SlackNotification(webhook_url))
    
    def add_notification_channel(self, channel: NotificationChannel):
        """添加通知渠道"""
        self.notification_channels[channel.name] = channel
    
    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules[rule.name] = rule
    
    def remove_alert_rule(self, rule_name: str) -> bool:
        """移除告警规则"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            return True
        return False
    
    async def evaluate_rules(self, metrics_data: Dict[str, Any] = None, 
                           health_status: HealthStatus = None) -> List[Alert]:
        """评估告警规则"""
        triggered_alerts = []
        
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            # 评估规则表达式
            if await self._evaluate_expression(rule.expression, metrics_data, health_status):
                # 检查是否已有活跃告警
                alert_fingerprint = f"{rule_name}_{hash(rule.expression)}"
                
                if alert_fingerprint not in self.active_alerts:
                    # 创建新告警
                    alert = Alert(
                        id=f"alert_{int(datetime.utcnow().timestamp())}",
                        rule_name=rule_name,
                        level=rule.level,
                        summary=rule.description,
                        description=f"规则 '{rule_name}' 被触发: {rule.expression}",
                        status=AlertState.FIRING,
                        start_time=datetime.utcnow(),
                        labels=rule.labels,
                        annotations=rule.annotations,
                        fingerprint=alert_fingerprint
                    )
                    
                    self.active_alerts[alert_fingerprint] = alert
                    triggered_alerts.append(alert)
                    
                    # 发送通知
                    await self._send_notifications(alert)
        
        # 检查已解决的告警
        resolved_alerts = []
        for fingerprint, alert in list(self.active_alerts.items()):
            rule = self.rules.get(alert.rule_name)
            if rule and not await self._evaluate_expression(rule.expression, metrics_data, health_status):
                # 告警已解决
                alert.status = AlertState.RESOLVED
                alert.end_time = datetime.utcnow()
                resolved_alerts.append(alert)
                del self.active_alerts[fingerprint]
                
                # 发送恢复通知
                await self._send_notifications(alert)
        
        # 保存到历史记录
        self.alert_history.extend(triggered_alerts + resolved_alerts)
        self._cleanup_old_alerts()
        
        return triggered_alerts
    
    async def _evaluate_expression(self, expression: str, metrics_data: Dict[str, Any], 
                                 health_status: HealthStatus) -> bool:
        """评估告警表达式"""
        try:
            # 这里应该实现真正的表达式解析和评估
            # 简化实现：支持一些基本的条件判断
            if "health_status" in expression:
                if "UNHEALTHY" in expression and health_status == HealthStatus.UNHEALTHY:
                    return True
                elif "DEGRADED" in expression and health_status == HealthStatus.DEGRADED:
                    return True
            
            if "cpu_usage" in expression and metrics_data:
                cpu_threshold = self.config.cpu_threshold_critical
                if metrics_data.get("cpu_usage_percent", 0) > cpu_threshold:
                    return True
            
            if "memory_usage" in expression and metrics_data:
                mem_threshold = self.config.memory_threshold_critical
                if metrics_data.get("memory_usage_percent", 0) > mem_threshold:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"表达式评估失败: {expression}, 错误: {str(e)}")
            return False
    
    async def _send_notifications(self, alert: Alert):
        """发送通知"""
        for channel in self.notification_channels.values():
            if channel.enabled:
                try:
                    await channel.send_notification(alert)
                except Exception as e:
                    self.logger.error(f"通知发送失败 ({channel.name}): {str(e)}")
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """获取告警历史"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [alert for alert in self.alert_history if alert.start_time >= cutoff_time]
    
    def _cleanup_old_alerts(self):
        """清理旧告警记录"""
        retention_cutoff = datetime.utcnow() - timedelta(days=self.config.alert_retention_days)
        self.alert_history = [
            alert for alert in self.alert_history 
            if alert.start_time >= retention_cutoff
        ]


# 默认告警规则
default_alert_rules = [
    AlertRule(
        name="high_cpu_usage",
        expression="cpu_usage_percent > 90",
        level=AlertLevel.CRITICAL,
        description="CPU 使用率过高",
        labels={"severity": "critical"},
        annotations={"summary": "系统负载过高，请及时处理"}
    ),
    AlertRule(
        name="high_memory_usage",
        expression="memory_usage_percent > 90",
        level=AlertLevel.ERROR,
        description="内存使用率过高",
        labels={"severity": "high"},
        annotations={"summary": "内存资源紧张"}
    ),
    AlertRule(
        name="system_unhealthy",
        expression="health_status == UNHEALTHY",
        level=AlertLevel.CRITICAL,
        description="系统健康状态异常",
        labels={"severity": "critical"},
        annotations={"summary": "系统核心服务出现故障"}
    )
]


# 全局告警管理器实例
alert_manager = AlertManager()

# 添加默认告警规则
for rule in default_alert_rules:
    alert_manager.add_alert_rule(rule)