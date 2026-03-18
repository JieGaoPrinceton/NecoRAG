# -*- coding: utf-8 -*-
"""
响应接口测试 - 用户配置、语气适配、详细度适配、可视化
"""

import pytest
from datetime import datetime

from src.response import ResponseInterface
from src.response.profile_manager import UserProfileManager
from src.response.tone_adapter import ToneAdapter
from src.response.detail_adapter import DetailLevelAdapter
from src.response.visualizer import ThinkingChainVisualizer
from src.response.models import UserProfile, Response, Interaction
from src.memory import MemoryManager, WorkingMemory
from src.refinement.models import RefinementResult, HallucinationReport


# ═══════════════════════════════════════════════════════════
# ToneAdapter 测试
# ═══════════════════════════════════════════════════════════

class TestToneAdapter:
    """语气适配器测试"""

    def test_init(self):
        adapter = ToneAdapter()
        assert adapter is not None

    def test_formal_tone(self):
        adapter = ToneAdapter()
        result = adapter.adapt("这是一段技术说明。", style="formal")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_friendly_tone(self):
        adapter = ToneAdapter()
        result = adapter.adapt("这是一段技术说明。", style="friendly")
        assert isinstance(result, str)

    def test_humorous_tone(self):
        adapter = ToneAdapter()
        result = adapter.adapt("这是一段技术说明。", style="humorous")
        assert isinstance(result, str)

    def test_inject_personality(self):
        adapter = ToneAdapter()
        result = adapter.inject_personality("原始内容", style="friendly")
        assert isinstance(result, str)

    def test_unknown_style_fallback(self):
        """未知风格不应崩溃"""
        adapter = ToneAdapter()
        result = adapter.adapt("内容", style="unknown_style")
        assert isinstance(result, str)


# ═══════════════════════════════════════════════════════════
# DetailLevelAdapter 测试
# ═══════════════════════════════════════════════════════════

class TestDetailLevelAdapter:
    """详细度适配器测试"""

    def test_init(self):
        adapter = DetailLevelAdapter()
        assert adapter is not None

    def test_level_1_brief(self):
        adapter = DetailLevelAdapter()
        content = "这是一段比较长的内容。\n它包含了多行文本。\n用于测试简要模式。"
        result = adapter.adapt(content, level=1)
        assert isinstance(result, str)

    def test_level_2_standard(self):
        adapter = DetailLevelAdapter()
        result = adapter.adapt("标准内容", level=2)
        assert isinstance(result, str)

    def test_level_3_detailed(self):
        adapter = DetailLevelAdapter()
        result = adapter.adapt("需要展开的内容", level=3)
        assert isinstance(result, str)

    def test_level_4_comprehensive(self):
        adapter = DetailLevelAdapter()
        result = adapter.adapt("需要深入分析的内容", level=4)
        assert isinstance(result, str)

    def test_summarize(self):
        adapter = DetailLevelAdapter()
        result = adapter.summarize("长文本\n多行\n需要总结")
        assert isinstance(result, str)

    def test_expand(self):
        adapter = DetailLevelAdapter()
        result = adapter.expand("简短文本")
        assert isinstance(result, str)


# ═══════════════════════════════════════════════════════════
# ThinkingChainVisualizer 测试
# ═══════════════════════════════════════════════════════════

class TestThinkingChainVisualizer:
    """思维链可视化测试"""

    def test_init(self):
        viz = ThinkingChainVisualizer()
        assert viz is not None

    def test_visualize(self):
        viz = ThinkingChainVisualizer()
        trace = ["步骤1: 查询解析", "步骤2: 向量检索"]
        evidence = [
            {"source": "机器学习定义", "score": 0.9},
            {"source": "深度学习概念", "score": 0.8},
        ]
        reasoning = ["推理1: 基于证据1", "推理2: 综合分析"]
        result = viz.visualize(trace, evidence, reasoning)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_visualize_empty(self):
        viz = ThinkingChainVisualizer()
        result = viz.visualize([], [], [])
        assert isinstance(result, str)

    def test_visualize_as_dict(self):
        viz = ThinkingChainVisualizer()
        result = viz.visualize_as_dict(
            retrieval_trace=["step1"],
            evidence=["evidence1"],
            reasoning_chain=["reason1"],
        )
        assert hasattr(result, "retrieval_steps") or isinstance(result, dict)


# ═══════════════════════════════════════════════════════════
# UserProfileManager 测试
# ═══════════════════════════════════════════════════════════

class TestUserProfileManager:
    """用户配置管理器测试"""

    def test_init(self, working_memory):
        manager = UserProfileManager(working_memory)
        assert manager is not None

    def test_get_profile_new_user(self, working_memory):
        manager = UserProfileManager(working_memory)
        profile = manager.get_profile("new-user")
        assert isinstance(profile, UserProfile)
        assert profile.user_id == "new-user"

    def test_get_profile_returns_same(self, working_memory):
        """同一用户应返回相同配置"""
        manager = UserProfileManager(working_memory)
        p1 = manager.get_profile("user-1")
        p2 = manager.get_profile("user-1")
        assert p1.user_id == p2.user_id

    def test_detect_style(self, working_memory):
        manager = UserProfileManager(working_memory)
        style = manager.detect_style("user-1")
        assert isinstance(style, str)

    def test_detect_professional_level(self, working_memory):
        manager = UserProfileManager(working_memory)
        level = manager.detect_professional_level("user-1")
        assert isinstance(level, str)


# ═══════════════════════════════════════════════════════════
# ResponseInterface 集成测试
# ═══════════════════════════════════════════════════════════

class TestResponseInterface:
    """响应接口集成测试"""

    def test_init(self, memory_manager):
        interface = ResponseInterface(memory=memory_manager)
        assert interface is not None

    def test_respond(self, memory_manager):
        interface = ResponseInterface(memory=memory_manager)
        refinement_result = RefinementResult(
            query="什么是AI？",
            answer="人工智能是计算机科学的一个分支。",
            confidence=0.85,
            citations=["source1"],
            hallucination_report=None,
            iterations=1,
        )
        response = interface.respond(
            query="什么是AI？",
            refinement_result=refinement_result,
        )
        assert isinstance(response, Response)
        assert len(response.content) > 0
        assert response.detail_level > 0

    def test_respond_with_tone(self, memory_manager):
        interface = ResponseInterface(memory=memory_manager)
        refinement_result = RefinementResult(
            query="解释深度学习",
            answer="深度学习使用多层神经网络处理数据。",
            confidence=0.9,
            citations=[],
            hallucination_report=None,
            iterations=1,
        )
        response = interface.respond(
            query="解释深度学习",
            refinement_result=refinement_result,
            tone="formal",
        )
        assert isinstance(response, Response)

    def test_get_user_preference(self, memory_manager):
        interface = ResponseInterface(memory=memory_manager)
        pref = interface.get_user_preference("test-user")
        assert isinstance(pref, dict)
