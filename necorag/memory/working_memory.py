"""
L1 工作记忆 (Redis)
存储当前会话上下文、用户意图轨迹
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from necorag.memory.models import Intent


class WorkingMemory:
    """
    L1 工作记忆
    
    特性：
    - 极低延迟访问
    - TTL 自动过期
    - LRU 淘汰策略
    - 模拟瞬时遗忘
    """
    
    def __init__(self, ttl: int = 3600, max_session_items: int = 1000):
        """
        初始化工作记忆
        
        Args:
            ttl: 会话 TTL（秒）
            max_session_items: 单会话最大条目
        """
        self.ttl = ttl
        self.max_session_items = max_session_items
        # 最小实现：使用内存字典模拟 Redis
        self._store: Dict[str, Dict[str, Any]] = {}
        self._sessions: Dict[str, List[Intent]] = {}
    
    def add_context(self, session_id: str, context: Dict[str, Any]) -> None:
        """
        添加会话上下文
        
        Args:
            session_id: 会话 ID
            context: 上下文数据
        """
        if session_id not in self._store:
            self._store[session_id] = {}
        
        self._store[session_id].update(context)
        self._store[session_id]["_last_update"] = datetime.now()
    
    def get_context(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话上下文
        
        Args:
            session_id: 会话 ID
            
        Returns:
            Dict: 上下文数据
        """
        return self._store.get(session_id, {})
    
    def track_intent(self, session_id: str, intent: Intent) -> None:
        """
        跟踪用户意图轨迹
        
        Args:
            session_id: 会话 ID
            intent: 用户意图
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        
        self._sessions[session_id].append(intent)
    
    def get_intent_trajectory(self, session_id: str) -> List[Intent]:
        """
        获取用户意图轨迹
        
        Args:
            session_id: 会话 ID
            
        Returns:
            List[Intent]: 意图列表
        """
        return self._sessions.get(session_id, [])
    
    def clear_session(self, session_id: str) -> None:
        """
        清除会话数据（模拟遗忘）
        
        Args:
            session_id: 会话 ID
        """
        self._store.pop(session_id, None)
        self._sessions.pop(session_id, None)
    
    def clear_expired(self) -> int:
        """
        清除过期数据
        
        Returns:
            int: 清除的条目数
            
        TODO: 实现 TTL 过期检测
        """
        # 最小实现：返回 0
        return 0
    
    def exists(self, session_id: str) -> bool:
        """
        检查会话是否存在
        
        Args:
            session_id: 会话 ID
            
        Returns:
            bool: 是否存在
        """
        return session_id in self._store
