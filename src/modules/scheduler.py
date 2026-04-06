"""
Update Scheduler - 更新任务调度器

管理定时批量更新任务的调度执行，支持 cron 式调度和间隔调度。
"""

from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import logging
import threading
import time
import uuid

from .models import UpdateTask, UpdateStatus, UpdateMode
from .config import KnowledgeEvolutionConfig


logger = logging.getLogger(__name__)


class ScheduledTask:
    """
    调度任务配置
    
    A scheduled task configuration.
    """
    
    def __init__(
        self,
        task_id: str,
        task_type: str,
        interval: Optional[int] = None,
        time_of_day: Optional[str] = None,
        callback: Optional[Callable] = None,
        enabled: bool = True
    ):
        """
        初始化调度任务
        
        Args:
            task_id: 任务 ID
            task_type: 任务类型（batch_update/index_rebuild/metrics_calc）
            interval: 执行间隔（秒）
            time_of_day: 每日执行时间（HH:MM）
            callback: 执行回调函数
            enabled: 是否启用
        """
        self.task_id = task_id
        self.task_type = task_type
        self.interval = interval
        self.time_of_day = time_of_day
        self.callback = callback
        self.enabled = enabled
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count: int = 0
        self.error_count: int = 0
        self.last_error: Optional[str] = None
        
        # 计算下次执行时间
        self._calculate_next_run()
    
    def _calculate_next_run(self):
        """计算下次执行时间"""
        now = datetime.now()
        
        if self.interval:
            # 间隔调度
            if self.last_run:
                self.next_run = self.last_run + timedelta(seconds=self.interval)
            else:
                self.next_run = now + timedelta(seconds=self.interval)
        
        elif self.time_of_day:
            # 定时调度（每日固定时间）
            try:
                hour, minute = map(int, self.time_of_day.split(':'))
                scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if scheduled_time <= now:
                    # 如果今天的时间已过，安排到明天
                    scheduled_time += timedelta(days=1)
                
                self.next_run = scheduled_time
            except ValueError:
                logger.error(f"Invalid time_of_day format: {self.time_of_day}")
                self.next_run = now + timedelta(hours=24)
    
    def should_run(self) -> bool:
        """检查是否应该执行"""
        if not self.enabled:
            return False
        if self.next_run is None:
            return False
        return datetime.now() >= self.next_run
    
    def mark_run(self, success: bool = True, error: Optional[str] = None):
        """标记执行完成"""
        self.last_run = datetime.now()
        self.run_count += 1
        
        if not success:
            self.error_count += 1
            self.last_error = error
        
        self._calculate_next_run()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "interval": self.interval,
            "time_of_day": self.time_of_day,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
        }


class UpdateScheduler:
    """
    更新任务调度器
    
    管理定时批量更新任务的调度执行。
    支持 cron 式调度和间隔调度。
    
    Update task scheduler that manages scheduled batch update tasks.
    Supports cron-style scheduling and interval-based scheduling.
    
    Note: 当前为简化实现，使用内置 threading 模块。
    在生产环境中应集成 APScheduler 或 Celery。
    """
    
    def __init__(
        self,
        config: Optional[KnowledgeEvolutionConfig] = None,
        updater: Any = None,
        metrics_calculator: Any = None
    ):
        """
        初始化调度器
        
        Args:
            config: 知识演化配置
            updater: 知识更新管理器实例
            metrics_calculator: 指标计算器实例
        """
        self.config = config or KnowledgeEvolutionConfig.default()
        self.updater = updater
        self.metrics_calculator = metrics_calculator
        
        # 调度任务列表
        self._scheduled_tasks: Dict[str, ScheduledTask] = {}
        
        # 运行状态
        self._is_running: bool = False
        self._scheduler_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # 执行日志
        self._execution_log: List[Dict[str, Any]] = []
        
        logger.info("UpdateScheduler initialized")
    
    def schedule_batch_update(
        self,
        interval: Optional[int] = None,
        time_of_day: Optional[str] = None
    ) -> str:
        """
        调度定时批量更新任务
        
        Args:
            interval: 执行间隔（秒），默认使用配置值
            time_of_day: 每日执行时间（HH:MM），默认使用配置值
            
        Returns:
            str: 任务 ID
        """
        task_id = f"batch_update_{uuid.uuid4().hex[:8]}"
        
        task = ScheduledTask(
            task_id=task_id,
            task_type="batch_update",
            interval=interval or self.config.batch_update_interval,
            time_of_day=time_of_day or self.config.batch_update_time,
            callback=self._execute_batch_update,
            enabled=self.config.enable_scheduled_update,
        )
        
        self._scheduled_tasks[task_id] = task
        logger.info(f"Scheduled batch update task: {task_id}")
        return task_id
    
    def schedule_index_rebuild(self, interval: Optional[int] = None) -> str:
        """
        调度索引重建任务
        
        Args:
            interval: 执行间隔（秒），默认使用配置值
            
        Returns:
            str: 任务 ID
        """
        task_id = f"index_rebuild_{uuid.uuid4().hex[:8]}"
        
        task = ScheduledTask(
            task_id=task_id,
            task_type="index_rebuild",
            interval=interval or self.config.index_rebuild_interval,
            callback=self._execute_index_rebuild,
            enabled=True,
        )
        
        self._scheduled_tasks[task_id] = task
        logger.info(f"Scheduled index rebuild task: {task_id}")
        return task_id
    
    def schedule_metrics_calculation(self, interval: Optional[int] = None) -> str:
        """
        调度指标计算任务
        
        Args:
            interval: 执行间隔（秒），默认使用配置值
            
        Returns:
            str: 任务 ID
        """
        task_id = f"metrics_calc_{uuid.uuid4().hex[:8]}"
        
        task = ScheduledTask(
            task_id=task_id,
            task_type="metrics_calculation",
            interval=interval or self.config.metrics_calculation_interval,
            callback=self._execute_metrics_calculation,
            enabled=True,
        )
        
        self._scheduled_tasks[task_id] = task
        logger.info(f"Scheduled metrics calculation task: {task_id}")
        return task_id
    
    def schedule_custom_task(
        self,
        task_type: str,
        callback: Callable,
        interval: Optional[int] = None,
        time_of_day: Optional[str] = None
    ) -> str:
        """
        调度自定义任务
        
        Args:
            task_type: 任务类型名称
            callback: 执行回调函数
            interval: 执行间隔（秒）
            time_of_day: 每日执行时间（HH:MM）
            
        Returns:
            str: 任务 ID
        """
        task_id = f"{task_type}_{uuid.uuid4().hex[:8]}"
        
        task = ScheduledTask(
            task_id=task_id,
            task_type=task_type,
            interval=interval,
            time_of_day=time_of_day,
            callback=callback,
            enabled=True,
        )
        
        self._scheduled_tasks[task_id] = task
        logger.info(f"Scheduled custom task: {task_id}")
        return task_id
    
    def _execute_batch_update(self) -> bool:
        """执行批量更新"""
        if self.updater is None:
            logger.warning("No updater configured for batch update")
            return False
        
        try:
            # 创建并执行批量更新任务
            task = self.updater.create_batch_update_task("Scheduled batch update")
            result = self.updater.execute_batch_update(task.task_id)
            
            success = result.status == UpdateStatus.COMPLETED
            logger.info(f"Batch update completed: {result.items_processed} items")
            return success
            
        except Exception as e:
            logger.error(f"Batch update failed: {e}")
            return False
    
    def _execute_index_rebuild(self) -> bool:
        """执行索引重建"""
        # TODO: 实现索引重建逻辑
        logger.info("Index rebuild executed (placeholder)")
        return True
    
    def _execute_metrics_calculation(self) -> bool:
        """执行指标计算"""
        if self.metrics_calculator is None:
            logger.warning("No metrics calculator configured")
            return False
        
        try:
            metrics = self.metrics_calculator.calculate_metrics(force_refresh=True)
            logger.info(f"Metrics calculated: health_score={metrics.health_score}")
            return True
            
        except Exception as e:
            logger.error(f"Metrics calculation failed: {e}")
            return False
    
    def start(self):
        """
        启动调度器
        
        Note: 当前为简化实现，使用后台线程轮询。
        在生产环境中应集成 APScheduler 或 Celery。
        """
        if self._is_running:
            logger.warning("Scheduler is already running")
            return
        
        self._is_running = True
        self._stop_event.clear()
        
        # 启动调度线程
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="KnowledgeEvolutionScheduler"
        )
        self._scheduler_thread.start()
        
        logger.info("Scheduler started")
    
    def _scheduler_loop(self):
        """调度循环"""
        while not self._stop_event.is_set():
            try:
                self._check_and_run_tasks()
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
            
            # 每分钟检查一次
            self._stop_event.wait(60)
    
    def _check_and_run_tasks(self):
        """检查并执行到期任务"""
        for task_id, task in self._scheduled_tasks.items():
            if task.should_run():
                logger.info(f"Running scheduled task: {task_id}")
                
                try:
                    if task.callback:
                        success = task.callback()
                    else:
                        success = True
                    
                    task.mark_run(success=success)
                    
                    # 记录执行日志
                    self._execution_log.append({
                        "task_id": task_id,
                        "task_type": task.task_type,
                        "timestamp": datetime.now().isoformat(),
                        "success": success,
                    })
                    
                except Exception as e:
                    task.mark_run(success=False, error=str(e))
                    logger.error(f"Task {task_id} failed: {e}")
    
    def stop(self):
        """停止调度器"""
        if not self._is_running:
            return
        
        self._stop_event.set()
        self._is_running = False
        
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        
        logger.info("Scheduler stopped")
    
    def get_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """
        获取已调度的任务列表
        
        Returns:
            List[Dict]: 任务列表
        """
        return [task.to_dict() for task in self._scheduled_tasks.values()]
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """
        获取指定任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            Optional[ScheduledTask]: 任务对象
        """
        return self._scheduled_tasks.get(task_id)
    
    def enable_task(self, task_id: str) -> bool:
        """
        启用任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            bool: 是否成功
        """
        task = self._scheduled_tasks.get(task_id)
        if task:
            task.enabled = True
            logger.info(f"Task enabled: {task_id}")
            return True
        return False
    
    def disable_task(self, task_id: str) -> bool:
        """
        禁用任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            bool: 是否成功
        """
        task = self._scheduled_tasks.get(task_id)
        if task:
            task.enabled = False
            logger.info(f"Task disabled: {task_id}")
            return True
        return False
    
    def remove_task(self, task_id: str) -> bool:
        """
        移除任务
        
        Args:
            task_id: 任务 ID
            
        Returns:
            bool: 是否成功
        """
        if task_id in self._scheduled_tasks:
            del self._scheduled_tasks[task_id]
            logger.info(f"Task removed: {task_id}")
            return True
        return False
    
    def get_next_run_time(self, task_id: str) -> Optional[datetime]:
        """
        获取下次执行时间
        
        Args:
            task_id: 任务 ID
            
        Returns:
            Optional[datetime]: 下次执行时间
        """
        task = self._scheduled_tasks.get(task_id)
        if task:
            return task.next_run
        return None
    
    def trigger_task(self, task_id: str) -> bool:
        """
        立即触发任务执行
        
        Args:
            task_id: 任务 ID
            
        Returns:
            bool: 是否成功
        """
        task = self._scheduled_tasks.get(task_id)
        if task is None:
            return False
        
        try:
            if task.callback:
                success = task.callback()
            else:
                success = True
            
            task.mark_run(success=success)
            return success
            
        except Exception as e:
            task.mark_run(success=False, error=str(e))
            logger.error(f"Manual trigger failed for {task_id}: {e}")
            return False
    
    def get_execution_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取执行日志
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 执行日志列表
        """
        return self._execution_log[-limit:]
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取调度器状态
        
        Returns:
            Dict: 状态信息
        """
        return {
            "is_running": self._is_running,
            "total_tasks": len(self._scheduled_tasks),
            "enabled_tasks": len([t for t in self._scheduled_tasks.values() if t.enabled]),
            "total_executions": sum(t.run_count for t in self._scheduled_tasks.values()),
            "total_errors": sum(t.error_count for t in self._scheduled_tasks.values()),
        }
    
    def setup_default_tasks(self):
        """
        设置默认调度任务
        
        根据配置自动创建常用的调度任务。
        """
        # 批量更新任务
        if self.config.enable_scheduled_update:
            self.schedule_batch_update()
        
        # 索引重建任务
        if self.config.index_rebuild_interval > 0:
            self.schedule_index_rebuild()
        
        # 指标计算任务
        if self.config.metrics_calculation_interval > 0:
            self.schedule_metrics_calculation()
        
        logger.info("Default scheduled tasks set up")


# APScheduler 集成支持（可选）
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False


class APSchedulerAdapter:
    """
    APScheduler 适配器
    
    提供与 APScheduler 库的集成支持。
    需要安装 apscheduler>=3.10.0
    
    APScheduler adapter that provides integration with the APScheduler library.
    Requires apscheduler>=3.10.0 to be installed.
    """
    
    def __init__(
        self,
        config: Optional[KnowledgeEvolutionConfig] = None,
        updater: Any = None,
        metrics_calculator: Any = None
    ):
        """
        初始化 APScheduler 适配器
        
        Args:
            config: 知识演化配置
            updater: 知识更新管理器实例
            metrics_calculator: 指标计算器实例
        """
        if not HAS_APSCHEDULER:
            raise ImportError("APScheduler is not installed. Install it with: pip install apscheduler>=3.10.0")
        
        self.config = config or KnowledgeEvolutionConfig.default()
        self.updater = updater
        self.metrics_calculator = metrics_calculator
        
        self._scheduler = BackgroundScheduler()
        self._job_ids: Dict[str, str] = {}
        
        logger.info("APSchedulerAdapter initialized")
    
    def schedule_batch_update(
        self,
        interval: Optional[int] = None,
        time_of_day: Optional[str] = None
    ) -> str:
        """调度批量更新任务"""
        job_id = f"batch_update_{uuid.uuid4().hex[:8]}"
        
        if time_of_day:
            hour, minute = map(int, time_of_day.split(':'))
            trigger = CronTrigger(hour=hour, minute=minute)
        else:
            interval = interval or self.config.batch_update_interval
            trigger = IntervalTrigger(seconds=interval)
        
        self._scheduler.add_job(
            self._execute_batch_update,
            trigger=trigger,
            id=job_id,
            name="Batch Update",
        )
        
        self._job_ids["batch_update"] = job_id
        return job_id
    
    def _execute_batch_update(self):
        """执行批量更新"""
        if self.updater is None:
            return
        
        try:
            task = self.updater.create_batch_update_task("Scheduled batch update (APScheduler)")
            self.updater.execute_batch_update(task.task_id)
        except Exception as e:
            logger.error(f"APScheduler batch update failed: {e}")
    
    def start(self):
        """启动调度器"""
        self._scheduler.start()
        logger.info("APScheduler started")
    
    def stop(self):
        """停止调度器"""
        self._scheduler.shutdown()
        logger.info("APScheduler stopped")
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """获取所有任务"""
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            }
            for job in self._scheduler.get_jobs()
        ]


def create_scheduler(
    config: Optional[KnowledgeEvolutionConfig] = None,
    updater: Any = None,
    metrics_calculator: Any = None,
    use_apscheduler: bool = False
):
    """
    创建调度器的便捷函数
    
    Args:
        config: 知识演化配置
        updater: 知识更新管理器实例
        metrics_calculator: 指标计算器实例
        use_apscheduler: 是否使用 APScheduler（需要安装）
        
    Returns:
        UpdateScheduler 或 APSchedulerAdapter 实例
    """
    if use_apscheduler:
        if not HAS_APSCHEDULER:
            logger.warning("APScheduler not available, falling back to built-in scheduler")
            return UpdateScheduler(config, updater, metrics_calculator)
        return APSchedulerAdapter(config, updater, metrics_calculator)
    
    return UpdateScheduler(config, updater, metrics_calculator)
