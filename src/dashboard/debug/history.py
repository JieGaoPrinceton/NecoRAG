"""
查询历史追踪服务 - Query History Tracking Service
管理调试查询的历史记录、检索和分析功能
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import json
import os

logger = logging.getLogger(__name__)


class QueryStatus(str, Enum):
    """查询状态枚举"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueryRecord:
    """查询记录数据模型"""
    query_id: str
    session_id: str
    query_text: str
    status: QueryStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    result_count: int = 0
    error_message: Optional[str] = None
    user_id: Optional[str] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'QueryRecord':
        """从字典创建实例"""
        data = data.copy()
        data['start_time'] = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            data['end_time'] = datetime.fromisoformat(data['end_time'])
        data['status'] = QueryStatus(data['status'])
        return cls(**data)


class QueryHistoryManager:
    """查询历史管理器"""
    
    def __init__(self, storage_path: str = "query_history.json", max_records: int = 10000):
        """
        初始化查询历史管理器
        
        Args:
            storage_path: 存储文件路径
            max_records: 最大记录数
        """
        self.storage_path = storage_path
        self.max_records = max_records
        self.records: List[QueryRecord] = []
        self.index_by_id: Dict[str, QueryRecord] = {}
        self.index_by_session: Dict[str, List[QueryRecord]] = {}
        self.lock = asyncio.Lock()
        
        # 加载历史记录
        self.load_history()
    
    def load_history(self):
        """从文件加载历史记录"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = [QueryRecord.from_dict(record) for record in data]
                    
                # 构建索引
                self._build_indices()
                logger.info(f"加载了 {len(self.records)} 条查询历史记录")
            else:
                logger.info("查询历史文件不存在，将创建新文件")
                
        except Exception as e:
            logger.error(f"加载查询历史失败: {e}")
            self.records = []
    
    def save_history(self):
        """保存历史记录到文件"""
        try:
            # 限制记录数量
            if len(self.records) > self.max_records:
                self.records = self.records[-self.max_records:]
                self._build_indices()
            
            # 转换为可序列化的格式
            serializable_records = [record.to_dict() for record in self.records]
            
            # 写入文件
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(serializable_records, f, ensure_ascii=False, indent=2)
                
            logger.debug(f"保存了 {len(self.records)} 条查询历史记录")
            
        except Exception as e:
            logger.error(f"保存查询历史失败: {e}")
    
    def _build_indices(self):
        """构建索引"""
        self.index_by_id = {}
        self.index_by_session = {}
        
        for record in self.records:
            self.index_by_id[record.query_id] = record
            
            if record.session_id not in self.index_by_session:
                self.index_by_session[record.session_id] = []
            self.index_by_session[record.session_id].append(record)
    
    async def add_record(self, record: QueryRecord):
        """
        添加查询记录
        
        Args:
            record: 查询记录
        """
        async with self.lock:
            self.records.append(record)
            self.index_by_id[record.query_id] = record
            
            if record.session_id not in self.index_by_session:
                self.index_by_session[record.session_id] = []
            self.index_by_session[record.session_id].append(record)
            
            # 自动保存
            self.save_history()
            
            logger.info(f"添加查询记录: {record.query_id}")
    
    async def update_record(self, query_id: str, **updates):
        """
        更新查询记录
        
        Args:
            query_id: 查询ID
            **updates: 要更新的字段
        """
        async with self.lock:
            if query_id in self.index_by_id:
                record = self.index_by_id[query_id]
                
                # 更新字段
                for key, value in updates.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                
                # 如果更新了结束时间，计算持续时间
                if 'end_time' in updates and record.start_time:
                    record.duration_ms = int(
                        (record.end_time - record.start_time).total_seconds() * 1000
                    )
                
                # 重新保存
                self.save_history()
                logger.info(f"更新查询记录: {query_id}")
    
    async def get_record(self, query_id: str) -> Optional[QueryRecord]:
        """
        获取单个查询记录
        
        Args:
            query_id: 查询ID
            
        Returns:
            查询记录或None
        """
        return self.index_by_id.get(query_id)
    
    async def get_session_queries(self, session_id: str) -> List[QueryRecord]:
        """
        获取会话的所有查询记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            查询记录列表
        """
        return self.index_by_session.get(session_id, [])
    
    async def search_records(self, 
                           query_text: Optional[str] = None,
                           status: Optional[QueryStatus] = None,
                           user_id: Optional[str] = None,
                           tags: Optional[List[str]] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           limit: int = 100) -> List[QueryRecord]:
        """
        搜索查询记录
        
        Args:
            query_text: 查询文本（模糊匹配）
            status: 查询状态
            user_id: 用户ID
            tags: 标签列表
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回记录数限制
            
        Returns:
            符合条件的查询记录列表
        """
        results = []
        
        for record in reversed(self.records):  # 从最新开始
            # 状态过滤
            if status and record.status != status:
                continue
                
            # 用户过滤
            if user_id and record.user_id != user_id:
                continue
                
            # 标签过滤
            if tags and not any(tag in record.tags for tag in tags):
                continue
                
            # 时间范围过滤
            if start_date and record.start_time < start_date:
                continue
            if end_date and record.start_time > end_date:
                continue
                
            # 文本搜索
            if query_text and query_text.lower() not in record.query_text.lower():
                continue
            
            results.append(record)
            
            if len(results) >= limit:
                break
        
        return results
    
    async def get_statistics(self, 
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        获取查询统计信息
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计信息字典
        """
        filtered_records = self.records
        
        # 时间范围过滤
        if start_date or end_date:
            filtered_records = [
                r for r in filtered_records
                if (not start_date or r.start_time >= start_date) and
                   (not end_date or r.start_time <= end_date)
            ]
        
        if not filtered_records:
            return {
                "total_queries": 0,
                "status_counts": {},
                "avg_duration": 0,
                "success_rate": 0
            }
        
        # 统计各项指标
        total_queries = len(filtered_records)
        status_counts = {}
        total_duration = 0
        successful_queries = 0
        
        for record in filtered_records:
            # 状态统计
            status = record.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # 持续时间统计
            if record.duration_ms:
                total_duration += record.duration_ms
            
            # 成功率统计
            if record.status in [QueryStatus.COMPLETED]:
                successful_queries += 1
        
        return {
            "total_queries": total_queries,
            "status_counts": status_counts,
            "avg_duration": total_duration / len([r for r in filtered_records if r.duration_ms]) if any(r.duration_ms for r in filtered_records) else 0,
            "success_rate": successful_queries / total_queries if total_queries > 0 else 0,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }
    
    async def delete_old_records(self, days: int = 30):
        """
        删除旧记录
        
        Args:
            days: 保留天数
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0
        
        async with self.lock:
            # 找到要删除的记录
            records_to_delete = [
                record for record in self.records
                if record.start_time < cutoff_date
            ]
            
            # 从主列表中移除
            for record in records_to_delete:
                self.records.remove(record)
                deleted_count += 1
                
                # 更新索引
                if record.query_id in self.index_by_id:
                    del self.index_by_id[record.query_id]
                
                if record.session_id in self.index_by_session:
                    self.index_by_session[record.session_id].remove(record)
                    if not self.index_by_session[record.session_id]:
                        del self.index_by_session[record.session_id]
            
            if deleted_count > 0:
                self.save_history()
                logger.info(f"删除了 {deleted_count} 条旧查询记录")
        
        return deleted_count


class QueryTracker:
    """查询追踪器 - 用于实时追踪正在进行的查询"""
    
    def __init__(self, history_manager: QueryHistoryManager):
        """
        初始化查询追踪器
        
        Args:
            history_manager: 查询历史管理器
        """
        self.history_manager = history_manager
        self.active_queries: Dict[str, QueryRecord] = {}
        self.lock = asyncio.Lock()
    
    async def start_tracking(self, 
                           query_id: str,
                           session_id: str,
                           query_text: str,
                           user_id: Optional[str] = None,
                           tags: Optional[List[str]] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> QueryRecord:
        """
        开始追踪查询
        
        Args:
            query_id: 查询ID
            session_id: 会话ID
            query_text: 查询文本
            user_id: 用户ID
            tags: 标签
            metadata: 元数据
            
        Returns:
            查询记录
        """
        async with self.lock:
            record = QueryRecord(
                query_id=query_id,
                session_id=session_id,
                query_text=query_text,
                status=QueryStatus.RUNNING,
                start_time=datetime.now(),
                user_id=user_id,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            self.active_queries[query_id] = record
            
            # 添加到历史记录
            await self.history_manager.add_record(record)
            
            logger.info(f"开始追踪查询: {query_id}")
            return record
    
    async def end_tracking(self, query_id: str, success: bool = True, error_message: Optional[str] = None):
        """
        结束查询追踪
        
        Args:
            query_id: 查询ID
            success: 是否成功
            error_message: 错误信息
        """
        async with self.lock:
            if query_id in self.active_queries:
                record = self.active_queries[query_id]
                
                # 更新记录
                status = QueryStatus.COMPLETED if success else QueryStatus.FAILED
                await self.history_manager.update_record(
                    query_id,
                    status=status,
                    end_time=datetime.now(),
                    error_message=error_message
                )
                
                # 移除活动查询
                del self.active_queries[query_id]
                
                logger.info(f"结束追踪查询: {query_id} (状态: {status.value})")
    
    async def cancel_tracking(self, query_id: str):
        """
        取消查询追踪
        
        Args:
            query_id: 查询ID
        """
        async with self.lock:
            if query_id in self.active_queries:
                record = self.active_queries[query_id]
                
                # 更新记录
                await self.history_manager.update_record(
                    query_id,
                    status=QueryStatus.CANCELLED,
                    end_time=datetime.now()
                )
                
                # 移除活动查询
                del self.active_queries[query_id]
                
                logger.info(f"取消追踪查询: {query_id}")
    
    async def get_active_queries(self) -> List[QueryRecord]:
        """获取所有活动查询"""
        return list(self.active_queries.values())
    
    async def get_query_status(self, query_id: str) -> Optional[QueryStatus]:
        """
        获取查询状态
        
        Args:
            query_id: 查询ID
            
        Returns:
            查询状态或None
        """
        if query_id in self.active_queries:
            return self.active_queries[query_id].status
        else:
            record = await self.history_manager.get_record(query_id)
            return record.status if record else None


# 使用示例和测试函数
async def demo_query_history():
    """演示查询历史功能"""
    
    # 创建历史管理器
    history_manager = QueryHistoryManager("test_query_history.json")
    
    # 创建查询追踪器
    tracker = QueryTracker(history_manager)
    
    # 模拟几个查询
    queries = [
        {
            "query_id": "qry_001",
            "session_id": "sess_001", 
            "query_text": "什么是人工智能？",
            "user_id": "user_001",
            "tags": ["faq", "ai"]
        },
        {
            "query_id": "qry_002",
            "session_id": "sess_001",
            "query_text": "机器学习算法有哪些？",
            "user_id": "user_001", 
            "tags": ["ml", "algorithms"]
        }
    ]
    
    # 开始追踪查询
    for query_data in queries:
        await tracker.start_tracking(**query_data)
    
    # 模拟查询完成
    await asyncio.sleep(1)
    await tracker.end_tracking("qry_001", success=True)
    
    await asyncio.sleep(1)
    await tracker.end_tracking("qry_002", success=False, error_message="检索超时")
    
    # 搜索查询记录
    recent_queries = await history_manager.search_records(limit=10)
    print(f"最近查询: {len(recent_queries)} 条")
    
    # 获取统计信息
    stats = await history_manager.get_statistics()
    print(f"统计信息: {stats}")
    
    # 清理测试文件
    if os.path.exists("test_query_history.json"):
        os.remove("test_query_history.json")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_query_history())