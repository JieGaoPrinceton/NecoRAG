# -*- coding: utf-8 -*-
"""
Dashboard 测试 - 配置管理器、数据模型
"""

import pytest
import json
from datetime import datetime

from src.dashboard.models import (
    RAGProfile,
    ModuleConfig,
    ModuleType,
    PerceptionConfig,
    MemoryConfig,
    RetrievalConfig,
    RefinementConfig,
    ResponseConfig,
    DashboardStats,
)
from src.dashboard.config_manager import ConfigManager


# ═══════════════════════════════════════════════════════════
# Dashboard 数据模型测试
# ═══════════════════════════════════════════════════════════

class TestModuleConfig:
    """模块配置测试"""

    def test_perception_config(self):
        config = PerceptionConfig()
        assert config.module_type == ModuleType.PERCEPTION
        assert config.enabled is True

    def test_memory_config(self):
        config = MemoryConfig()
        assert config.module_type == ModuleType.MEMORY

    def test_retrieval_config(self):
        config = RetrievalConfig()
        assert config.module_type == ModuleType.RETRIEVAL

    def test_refinement_config(self):
        config = RefinementConfig()
        assert config.module_type == ModuleType.REFINEMENT

    def test_response_config(self):
        config = ResponseConfig()
        assert config.module_type == ModuleType.RESPONSE

    def test_to_dict(self):
        config = PerceptionConfig()
        d = config.to_dict()
        assert isinstance(d, dict)
        assert "module_type" in d
        assert "parameters" in d

    def test_from_dict(self):
        config = PerceptionConfig()
        d = config.to_dict()
        restored = ModuleConfig.from_dict(d)
        assert isinstance(restored, ModuleConfig)
        assert restored.module_name == config.module_name


class TestRAGProfile:
    """RAG Profile 测试"""

    def test_create_profile(self):
        profile = RAGProfile(
            profile_id="test-profile",
            profile_name="Test",
            description="测试配置",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
            perception_config=PerceptionConfig(),
            memory_config=MemoryConfig(),
            retrieval_config=RetrievalConfig(),
            refinement_config=RefinementConfig(),
            response_config=ResponseConfig(),
        )
        assert profile.profile_id == "test-profile"

    def test_to_dict(self):
        profile = RAGProfile(
            profile_id="test",
            profile_name="Test",
            description="测试",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
            perception_config=PerceptionConfig(),
            memory_config=MemoryConfig(),
            retrieval_config=RetrievalConfig(),
            refinement_config=RefinementConfig(),
            response_config=ResponseConfig(),
        )
        d = profile.to_dict()
        assert isinstance(d, dict)
        assert d["profile_id"] == "test"

    def test_from_dict(self):
        profile = RAGProfile(
            profile_id="round-trip",
            profile_name="Round Trip",
            description="测试序列化",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=False,
            perception_config=PerceptionConfig(),
            memory_config=MemoryConfig(),
            retrieval_config=RetrievalConfig(),
            refinement_config=RefinementConfig(),
            response_config=ResponseConfig(),
        )
        d = profile.to_dict()
        restored = RAGProfile.from_dict(d)
        assert isinstance(restored, RAGProfile)
        assert restored.profile_id == "round-trip"

    def test_to_json_and_back(self):
        profile = RAGProfile(
            profile_id="json-test",
            profile_name="JSON",
            description="JSON 序列化",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
            perception_config=PerceptionConfig(),
            memory_config=MemoryConfig(),
            retrieval_config=RetrievalConfig(),
            refinement_config=RefinementConfig(),
            response_config=ResponseConfig(),
        )
        json_str = profile.to_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["profile_id"] == "json-test"
        restored = RAGProfile.from_json(json_str)
        assert isinstance(restored, RAGProfile)


class TestDashboardStats:
    """Dashboard 统计数据测试"""

    def test_default_stats(self):
        stats = DashboardStats()
        assert stats.total_documents == 0
        assert stats.total_queries == 0


# ═══════════════════════════════════════════════════════════
# ConfigManager 测试
# ═══════════════════════════════════════════════════════════

class TestConfigManager:
    """配置管理器测试"""

    def test_init(self, tmp_path):
        manager = ConfigManager(config_dir=str(tmp_path))
        assert manager is not None

    def test_create_profile(self, tmp_path):
        manager = ConfigManager(config_dir=str(tmp_path))
        profile = manager.create_profile("Test Profile", "A test profile")
        assert isinstance(profile, RAGProfile)
        assert profile.profile_name == "Test Profile"

    def test_list_profiles(self, tmp_path):
        manager = ConfigManager(config_dir=str(tmp_path))
        manager.create_profile("Profile 1", "First")
        profiles = manager.get_all_profiles()
        assert isinstance(profiles, list)
        assert len(profiles) >= 1

    def test_get_profile(self, tmp_path):
        manager = ConfigManager(config_dir=str(tmp_path))
        created = manager.create_profile("Get Test", "Test")
        retrieved = manager.get_profile(created.profile_id)
        assert retrieved is not None
        assert retrieved.profile_id == created.profile_id

    def test_delete_profile(self, tmp_path):
        manager = ConfigManager(config_dir=str(tmp_path))
        created = manager.create_profile("Delete Test", "Test")
        result = manager.delete_profile(created.profile_id)
        assert result is True

    def test_set_active_profile(self, tmp_path):
        manager = ConfigManager(config_dir=str(tmp_path))
        p = manager.create_profile("Active Test", "Test")
        result = manager.set_active_profile(p.profile_id)
        assert result is True
