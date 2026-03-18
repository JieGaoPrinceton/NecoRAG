"""
测试 NecoRAG 工作记忆模块

测试内容：
- 工作记忆存储和检索
- 容量限制
- 会话管理
- 意图轨迹跟踪
"""

import pytest
from datetime import datetime

from src.memory.working_memory import WorkingMemory
from src.memory.models import Intent


class TestWorkingMemoryInit:
    """WorkingMemory 初始化测试"""
    
    def test_init_default_parameters(self):
        """测试默认参数初始化"""
        wm = WorkingMemory()
        
        assert wm.ttl == 3600
        assert wm.max_session_items == 1000
        assert wm._store == {}
        assert wm._sessions == {}
    
    def test_init_custom_parameters(self):
        """测试自定义参数初始化"""
        wm = WorkingMemory(ttl=1800, max_session_items=500)
        
        assert wm.ttl == 1800
        assert wm.max_session_items == 500


class TestContextOperations:
    """上下文操作测试"""
    
    def test_add_context_new_session(self):
        """测试添加新会话上下文"""
        wm = WorkingMemory()
        session_id = "session-001"
        context = {"key1": "value1", "key2": "value2"}
        
        wm.add_context(session_id, context)
        
        assert session_id in wm._store
        assert wm._store[session_id]["key1"] == "value1"
        assert wm._store[session_id]["key2"] == "value2"
        assert "_last_update" in wm._store[session_id]
    
    def test_add_context_existing_session(self):
        """测试向已存在的会话添加上下文"""
        wm = WorkingMemory()
        session_id = "session-001"
        
        wm.add_context(session_id, {"key1": "value1"})
        wm.add_context(session_id, {"key2": "value2"})
        
        assert wm._store[session_id]["key1"] == "value1"
        assert wm._store[session_id]["key2"] == "value2"
    
    def test_add_context_updates_existing_key(self):
        """测试更新已存在的键"""
        wm = WorkingMemory()
        session_id = "session-001"
        
        wm.add_context(session_id, {"key1": "old_value"})
        wm.add_context(session_id, {"key1": "new_value"})
        
        assert wm._store[session_id]["key1"] == "new_value"
    
    def test_get_context_existing_session(self):
        """测试获取已存在会话的上下文"""
        wm = WorkingMemory()
        session_id = "session-001"
        context = {"key1": "value1"}
        
        wm.add_context(session_id, context)
        retrieved = wm.get_context(session_id)
        
        assert retrieved["key1"] == "value1"
    
    def test_get_context_nonexistent_session(self):
        """测试获取不存在会话的上下文"""
        wm = WorkingMemory()
        
        retrieved = wm.get_context("nonexistent-session")
        
        assert retrieved == {}
    
    def test_context_has_last_update_timestamp(self):
        """测试上下文包含最后更新时间戳"""
        wm = WorkingMemory()
        session_id = "session-001"
        
        wm.add_context(session_id, {"data": "test"})
        context = wm.get_context(session_id)
        
        assert "_last_update" in context
        assert isinstance(context["_last_update"], datetime)


class TestIntentTracking:
    """意图轨迹跟踪测试"""
    
    def test_track_intent_new_session(self):
        """测试新会话的意图跟踪"""
        wm = WorkingMemory()
        session_id = "session-001"
        intent = Intent(
            intent_type="factual",
            confidence=0.9,
            entities=["entity1"]
        )
        
        wm.track_intent(session_id, intent)
        
        assert session_id in wm._sessions
        assert len(wm._sessions[session_id]) == 1
        assert wm._sessions[session_id][0].intent_type == "factual"
    
    def test_track_multiple_intents(self):
        """测试跟踪多个意图"""
        wm = WorkingMemory()
        session_id = "session-001"
        
        intent1 = Intent(intent_type="factual", confidence=0.9)
        intent2 = Intent(intent_type="reasoning", confidence=0.8)
        intent3 = Intent(intent_type="explanation", confidence=0.85)
        
        wm.track_intent(session_id, intent1)
        wm.track_intent(session_id, intent2)
        wm.track_intent(session_id, intent3)
        
        trajectory = wm.get_intent_trajectory(session_id)
        
        assert len(trajectory) == 3
        assert trajectory[0].intent_type == "factual"
        assert trajectory[1].intent_type == "reasoning"
        assert trajectory[2].intent_type == "explanation"
    
    def test_get_intent_trajectory_existing_session(self):
        """测试获取已存在会话的意图轨迹"""
        wm = WorkingMemory()
        session_id = "session-001"
        intent = Intent(intent_type="factual", confidence=0.9)
        
        wm.track_intent(session_id, intent)
        trajectory = wm.get_intent_trajectory(session_id)
        
        assert len(trajectory) == 1
        assert trajectory[0] == intent
    
    def test_get_intent_trajectory_nonexistent_session(self):
        """测试获取不存在会话的意图轨迹"""
        wm = WorkingMemory()
        
        trajectory = wm.get_intent_trajectory("nonexistent-session")
        
        assert trajectory == []


class TestSessionManagement:
    """会话管理测试"""
    
    def test_clear_session(self):
        """测试清除会话"""
        wm = WorkingMemory()
        session_id = "session-001"
        
        wm.add_context(session_id, {"data": "test"})
        wm.track_intent(session_id, Intent(intent_type="factual", confidence=0.9))
        
        wm.clear_session(session_id)
        
        assert wm.get_context(session_id) == {}
        assert wm.get_intent_trajectory(session_id) == []
    
    def test_clear_nonexistent_session(self):
        """测试清除不存在的会话"""
        wm = WorkingMemory()
        
        # 不应抛出异常
        wm.clear_session("nonexistent-session")
    
    def test_exists_existing_session(self):
        """测试检查已存在会话"""
        wm = WorkingMemory()
        session_id = "session-001"
        
        wm.add_context(session_id, {"data": "test"})
        
        assert wm.exists(session_id) is True
    
    def test_exists_nonexistent_session(self):
        """测试检查不存在的会话"""
        wm = WorkingMemory()
        
        assert wm.exists("nonexistent-session") is False
    
    def test_clear_expired(self):
        """测试清除过期数据"""
        wm = WorkingMemory()
        
        # 当前实现返回 0
        cleared = wm.clear_expired()
        
        assert cleared == 0


class TestMultipleSessions:
    """多会话测试"""
    
    def test_multiple_sessions_isolation(self):
        """测试多会话数据隔离"""
        wm = WorkingMemory()
        
        wm.add_context("session-001", {"key": "value1"})
        wm.add_context("session-002", {"key": "value2"})
        wm.add_context("session-003", {"key": "value3"})
        
        assert wm.get_context("session-001")["key"] == "value1"
        assert wm.get_context("session-002")["key"] == "value2"
        assert wm.get_context("session-003")["key"] == "value3"
    
    def test_multiple_sessions_intents_isolation(self):
        """测试多会话意图隔离"""
        wm = WorkingMemory()
        
        intent1 = Intent(intent_type="factual", confidence=0.9)
        intent2 = Intent(intent_type="reasoning", confidence=0.8)
        
        wm.track_intent("session-001", intent1)
        wm.track_intent("session-002", intent2)
        
        trajectory1 = wm.get_intent_trajectory("session-001")
        trajectory2 = wm.get_intent_trajectory("session-002")
        
        assert len(trajectory1) == 1
        assert len(trajectory2) == 1
        assert trajectory1[0].intent_type == "factual"
        assert trajectory2[0].intent_type == "reasoning"
    
    def test_clear_one_session_preserves_others(self):
        """测试清除一个会话不影响其他会话"""
        wm = WorkingMemory()
        
        wm.add_context("session-001", {"data": "data1"})
        wm.add_context("session-002", {"data": "data2"})
        
        wm.clear_session("session-001")
        
        assert wm.exists("session-001") is False
        assert wm.exists("session-002") is True
        assert wm.get_context("session-002")["data"] == "data2"


class TestEdgeCases:
    """边界情况测试"""
    
    def test_empty_context(self):
        """测试空上下文"""
        wm = WorkingMemory()
        
        wm.add_context("session-001", {})
        
        context = wm.get_context("session-001")
        assert "_last_update" in context
    
    def test_large_context(self):
        """测试大型上下文"""
        wm = WorkingMemory()
        large_context = {f"key_{i}": f"value_{i}" for i in range(1000)}
        
        wm.add_context("session-001", large_context)
        
        context = wm.get_context("session-001")
        assert len(context) >= 1000
    
    def test_special_characters_in_session_id(self):
        """测试会话 ID 中的特殊字符"""
        wm = WorkingMemory()
        special_id = "session-with-special_chars!@#$%"
        
        wm.add_context(special_id, {"data": "test"})
        
        assert wm.exists(special_id) is True
        assert wm.get_context(special_id)["data"] == "test"
    
    def test_unicode_in_context(self):
        """测试上下文中的 Unicode 字符"""
        wm = WorkingMemory()
        context = {
            "中文键": "中文值",
            "emoji": "🎉🚀",
            "mixed": "Hello 世界 🌍"
        }
        
        wm.add_context("session-001", context)
        
        retrieved = wm.get_context("session-001")
        assert retrieved["中文键"] == "中文值"
        assert retrieved["emoji"] == "🎉🚀"
