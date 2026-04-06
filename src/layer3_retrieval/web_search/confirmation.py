"""
Human Confirmation Manager - 人工确认管理器
管理搜索结果的人工确认流程，包括请求创建、状态跟踪和超时处理
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Awaitable
from datetime import datetime, timedelta
import json

from .models import ConfirmationRequest, ConfirmationStatus, WebSearchResult

logger = logging.getLogger(__name__)


class HumanConfirmationManager:
    """
    人工确认管理器
    
    负责管理确认请求的生命周期，包括创建、跟踪、超时处理和回调通知
    """
    
    def __init__(self, 
                 confirmation_timeout: int = 300,
                 max_pending_requests: int = 100):
        """
        初始化确认管理器
        
        Args:
            confirmation_timeout: 确认超时时间（秒）
            max_pending_requests: 最大待处理请求数
        """
        self.confirmation_timeout = confirmation_timeout
        self.max_pending_requests = max_pending_requests
        self.requests: Dict[str, ConfirmationRequest] = {}
        self.callbacks: Dict[str, List[Callable]] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    async def start(self):
        """启动管理器"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("HumanConfirmationManager started")
    
    async def stop(self):
        """停止管理器"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("HumanConfirmationManager stopped")
    
    async def create_confirmation_request(
        self, 
        query: str, 
        search_results: List[WebSearchResult],
        timeout: Optional[int] = None
    ) -> ConfirmationRequest:
        """
        创建确认请求
        
        Args:
            query: 查询内容
            search_results: 搜索结果
            timeout: 超时时间（秒）
            
        Returns:
            ConfirmationRequest: 创建的确认请求
            
        Raises:
            RuntimeError: 当待处理请求数过多时
        """
        async with self._lock:
            if len(self.requests) >= self.max_pending_requests:
                raise RuntimeError("Too many pending confirmation requests")
            
            timeout = timeout or self.confirmation_timeout
            request = ConfirmationRequest(
                query=query,
                search_results=search_results,
                timeout=timeout
            )
            
            self.requests[request.request_id] = request
            self.callbacks[request.request_id] = []
            
            logger.info(f"Created confirmation request {request.request_id} "
                       f"with {len(search_results)} results")
            
            return request
    
    async def get_confirmation_request(self, request_id: str) -> Optional[ConfirmationRequest]:
        """
        获取确认请求
        
        Args:
            request_id: 请求ID
            
        Returns:
            Optional[ConfirmationRequest]: 确认请求
        """
        return self.requests.get(request_id)
    
    async def confirm_result(self, request_id: str, result_index: int, 
                           feedback: Optional[str] = None) -> bool:
        """
        确认结果
        
        Args:
            request_id: 请求ID
            result_index: 结果索引
            feedback: 用户反馈
            
        Returns:
            bool: 操作是否成功
        """
        async with self._lock:
            request = self.requests.get(request_id)
            if not request:
                logger.warning(f"Request {request_id} not found")
                return False
            
            success = request.confirm_result(result_index, feedback)
            if success:
                logger.info(f"Confirmed result {result_index} in request {request_id}")
                await self._trigger_callbacks(request_id, request)
                self._check_completion(request)
            
            return success
    
    async def reject_result(self, request_id: str, result_index: int,
                          feedback: Optional[str] = None) -> bool:
        """
        拒绝结果
        
        Args:
            request_id: 请求ID
            result_index: 结果索引
            feedback: 用户反馈
            
        Returns:
            bool: 操作是否成功
        """
        async with self._lock:
            request = self.requests.get(request_id)
            if not request:
                logger.warning(f"Request {request_id} not found")
                return False
            
            success = request.reject_result(result_index, feedback)
            if success:
                logger.info(f"Rejected result {result_index} in request {request_id}")
                await self._trigger_callbacks(request_id, request)
                self._check_completion(request)
            
            return success    
    async def add_callback(self, request_id: str, callback: Callable[[ConfirmationRequest], Awaitable[None]]):
        """
        添加回调函数
        
        Args:
            request_id: 请求ID
            callback: 回调函数
        """
        async with self._lock:
            if request_id in self.callbacks:
                self.callbacks[request_id].append(callback)
    
    async def remove_request(self, request_id: str) -> bool:
        """
        移除请求
        
        Args:
            request_id: 请求ID
            
        Returns:
            bool: 是否成功移除
        """
        async with self._lock:
            if request_id in self.requests:
                del self.requests[request_id]
                del self.callbacks[request_id]
                logger.info(f"Removed request {request_id}")
                return True
            return False
    
    async def get_pending_requests(self) -> List[ConfirmationRequest]:
        """
        获取所有待处理请求
        
        Returns:
            List[ConfirmationRequest]: 待处理请求列表
        """
        return [
            req for req in self.requests.values()
            if req.status == ConfirmationStatus.PENDING
        ]
    
    async def get_expired_requests(self) -> List[ConfirmationRequest]:
        """
        获取已过期请求
        
        Returns:
            List[ConfirmationRequest]: 已过期请求列表
        """
        return [
            req for req in self.requests.values()
            if req.is_expired
        ]
    
    def _check_completion(self, request: ConfirmationRequest):
        """
        检查请求是否完成
        
        Args:
            request: 确认请求
        """
        if request.status in [ConfirmationStatus.CONFIRMED, 
                             ConfirmationStatus.REJECTED, 
                             ConfirmationStatus.EXPIRED]:
            logger.info(f"Request {request.request_id} completed with status {request.status}")
    
    async def _trigger_callbacks(self, request_id: str, request: ConfirmationRequest):
        """
        触发回调函数
        
        Args:
            request_id: 请求ID
            request: 确认请求
        """
        callbacks = self.callbacks.get(request_id, [])
        for callback in callbacks:
            try:
                await callback(request)
            except Exception as e:
                logger.error(f"Callback error for request {request_id}: {e}")
    
    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                await self._cleanup_expired_requests()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_expired_requests(self):
        """清理过期请求"""
        expired_requests = await self.get_expired_requests()
        
        async with self._lock:
            for request in expired_requests:
                if request.status == ConfirmationStatus.PENDING:
                    request.status = ConfirmationStatus.EXPIRED
                    logger.info(f"Expired request {request.request_id}")
                    await self._trigger_callbacks(request.request_id, request)
                
                # 移除过期很久的请求（超过1小时）
                if datetime.now() > request.expires_at + timedelta(hours=1):
                    if request.request_id in self.requests:
                        del self.requests[request.request_id]
                    if request.request_id in self.callbacks:
                        del self.callbacks[request.request_id]
    
    async def export_requests(self, filepath: str):
        """
        导出请求数据
        
        Args:
            filepath: 导出文件路径
        """
        data = {
            'export_time': datetime.now().isoformat(),
            'requests': [req.to_dict() for req in self.requests.values()]
        }
        
        async with self._lock:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(self.requests)} requests to {filepath}")
    
    async def import_requests(self, filepath: str):
        """
        导入请求数据
        
        Args:
            filepath: 导入文件路径
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            imported_count = 0
            async with self._lock:
                for req_data in data.get('requests', []):
                    try:
                        # 重建ConfirmationRequest对象
                        request = ConfirmationRequest(
                            request_id=req_data['request_id'],
                            query=req_data['query'],
                            timeout=req_data['timeout']
                        )
                        
                        # 恢复其他属性
                        request.status = ConfirmationStatus(req_data['status'])
                        request.created_at = datetime.fromisoformat(req_data['created_at'])
                        request.expires_at = datetime.fromisoformat(req_data['expires_at'])
                        request.confirmed_indices = req_data['confirmed_indices']
                        request.rejected_indices = req_data['rejected_indices']
                        request.user_feedback = req_data['user_feedback']
                        
                        # 重建搜索结果
                        search_results = []
                        for result_data in req_data['search_results']:
                            result = WebSearchResult(
                                title=result_data['title'],
                                url=result_data['url'],
                                snippet=result_data['snippet'],
                                content=result_data['content'],
                                credibility_score=result_data['credibility_score'],
                                relevance_score=result_data['relevance_score']
                            )
                            # 恢复其他属性
                            result.timestamp = datetime.fromisoformat(result_data['timestamp'])
                            result.source = result_data['source']
                            result.domain = result_data['domain']
                            result.language = result_data['language']
                            result.metadata = result_data['metadata']
                            search_results.append(result)
                        
                        request.search_results = search_results
                        
                        self.requests[request.request_id] = request
                        self.callbacks[request.request_id] = []
                        imported_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to import request: {e}")
            
            logger.info(f"Imported {imported_count} requests from {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to import requests from {filepath}: {e}")


# 便捷的确认处理装饰器
def confirmation_required(timeout: int = 300):
    """
    装饰器：为函数添加确认要求
    
    Args:
        timeout: 确认超时时间
    """
    def decorator(func):
        async def wrapper(*args, confirmation_manager=None, **kwargs):
            if confirmation_manager is None:
                # 如果没有确认管理器，直接执行原函数
                return await func(*args, **kwargs)
            
            # 执行原函数获取搜索结果
            search_results = await func(*args, **kwargs)
            
            if not search_results:
                return search_results
            
            # 创建确认请求
            query = kwargs.get('query', 'Unknown query')
            request = await confirmation_manager.create_confirmation_request(
                query=query,
                search_results=search_results,
                timeout=timeout
            )
            
            # 这里应该返回请求ID给调用者，由调用者处理确认流程
            # 实际应用中可能需要更复杂的交互机制
            return {
                'request_id': request.request_id,
                'results': search_results,
                'requires_confirmation': True
            }
        
        return wrapper
    return decorator