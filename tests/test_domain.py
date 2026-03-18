# -*- coding: utf-8 -*-
"""
领域权重测试 - 复合权重计算、时序衰减、领域相关性
"""

import pytest
from datetime import datetime, timedelta

from src.domain import (
    DomainConfig,
    DomainConfigManager,
    KeywordLevel,
    DomainLevel,
    CompositeWeightCalculator,
    TemporalWeightCalculator,
    DomainRelevanceCalculator,
    create_example_domain,
)
from src.domain.weight_calculator import DocumentMetadata, WeightedScore, WeightCalculatorFactory
from src.domain.temporal_weight import TemporalWeightConfig, DecayPresets, TemporalTier


# ═══════════════════════════════════════════════════════════
# DomainConfig 测试
# ═══════════════════════════════════════════════════════════

class TestDomainConfig:
    """领域配置测试"""

    def test_create_example_domain(self):
        config = create_example_domain()
        assert isinstance(config, DomainConfig)
        assert config.domain_name is not None

    def test_domain_config_attributes(self, domain_config):
        assert hasattr(domain_config, "domain_name")
        assert hasattr(domain_config, "keywords")
        assert hasattr(domain_config, "decay_rate")

    def test_add_keyword(self, domain_config):
        domain_config.add_keyword(
            keyword="测试关键词",
            level=KeywordLevel.NORMAL,
            weight=1.0,
            aliases=["测试"],
            description="测试用",
        )
        assert "测试关键词" in domain_config.keywords

    def test_get_keyword_weight(self, domain_config):
        weight = domain_config.get_keyword_weight("不存在的关键词")
        assert isinstance(weight, float)

    def test_get_all_keywords(self, domain_config):
        keywords = domain_config.get_all_keywords()
        assert isinstance(keywords, set)

    def test_to_dict_and_back(self, domain_config):
        d = domain_config.to_dict()
        assert isinstance(d, dict)
        restored = DomainConfig.from_dict(d)
        assert isinstance(restored, DomainConfig)
        assert restored.domain_name == domain_config.domain_name


class TestDomainConfigManager:
    """领域配置管理器测试"""

    def test_init(self):
        manager = DomainConfigManager()
        assert manager is not None

    def test_create_domain(self):
        manager = DomainConfigManager()
        config = manager.create_domain("测试", "test-domain", "测试领域")
        assert isinstance(config, DomainConfig)
        assert config.domain_id == "test-domain"

    def test_get_domain(self):
        manager = DomainConfigManager()
        manager.create_domain("测试", "test-domain", "描述")
        config = manager.get_domain("test-domain")
        assert config is not None

    def test_get_nonexistent_domain(self):
        manager = DomainConfigManager()
        config = manager.get_domain("nonexistent")
        assert config is None

    def test_set_active_domain(self):
        manager = DomainConfigManager()
        manager.create_domain("测试", "test", "描述")
        result = manager.set_active_domain("test")
        assert result is True

    def test_list_domains(self):
        manager = DomainConfigManager()
        manager.create_domain("A", "a", "A domain")
        manager.create_domain("B", "b", "B domain")
        domains = manager.list_domains()
        assert len(domains) >= 2


# ═══════════════════════════════════════════════════════════
# TemporalWeightCalculator 测试
# ═══════════════════════════════════════════════════════════

class TestTemporalWeightCalculator:
    """时序权重计算器测试"""

    def test_init(self):
        calc = TemporalWeightCalculator()
        assert calc is not None

    def test_calculate_weight_recent(self):
        calc = TemporalWeightCalculator()
        now = datetime.now()
        weight = calc.calculate_weight(now - timedelta(days=1), now)
        assert weight >= 0.8  # 近期文档权重应高

    def test_calculate_weight_old(self):
        calc = TemporalWeightCalculator()
        now = datetime.now()
        weight = calc.calculate_weight(now - timedelta(days=3650), now)
        assert weight < 0.5  # 远古文档权重应低

    def test_evergreen_content(self):
        calc = TemporalWeightCalculator()
        now = datetime.now()
        weight = calc.calculate_weight(
            now - timedelta(days=3650), now, is_evergreen=True
        )
        assert weight > 0  # 常青内容应有较高权重

    def test_temporal_tiers(self):
        calc = TemporalWeightCalculator()
        now = datetime.now()
        tier = calc.get_temporal_tier(now - timedelta(days=1), now)
        assert tier == TemporalTier.RECENT

    def test_exponential_decay(self):
        calc = TemporalWeightCalculator()
        now = datetime.now()
        w1 = calc.calculate_exponential_decay(now - timedelta(days=1), now)
        w2 = calc.calculate_exponential_decay(now - timedelta(days=365), now)
        assert w1 > w2

    def test_weight_description(self):
        calc = TemporalWeightCalculator()
        desc = calc.get_weight_description(0.9)
        assert isinstance(desc, str)


class TestDecayPresets:
    """衰减预设测试"""

    def test_fast_changing(self):
        config = DecayPresets.fast_changing_domain()
        assert isinstance(config, TemporalWeightConfig)
        assert config.decay_rate > 0

    def test_normal(self):
        config = DecayPresets.normal_domain()
        assert isinstance(config, TemporalWeightConfig)

    def test_slow_changing(self):
        config = DecayPresets.slow_changing_domain()
        assert isinstance(config, TemporalWeightConfig)

    def test_evergreen(self):
        config = DecayPresets.evergreen_domain()
        assert isinstance(config, TemporalWeightConfig)


# ═══════════════════════════════════════════════════════════
# DomainRelevanceCalculator 测试
# ═══════════════════════════════════════════════════════════

class TestDomainRelevanceCalculator:
    """领域相关性计算器测试"""

    def test_init(self, domain_config):
        calc = DomainRelevanceCalculator(domain_config)
        assert calc is not None

    def test_calculate_relevance(self, domain_config):
        calc = DomainRelevanceCalculator(domain_config)
        result = calc.calculate_relevance("机器学习和深度学习的应用")
        assert hasattr(result, "score")
        assert 0 <= result.score <= 1

    def test_extract_keywords(self, domain_config):
        calc = DomainRelevanceCalculator(domain_config)
        keywords = calc.extract_keywords("人工智能领域的最新进展")
        assert isinstance(keywords, dict)

    def test_classify_domain_level(self, domain_config):
        calc = DomainRelevanceCalculator(domain_config)
        level = calc.classify_domain_level(0.8, 0.5)
        assert isinstance(level, DomainLevel)

    def test_batch_calculate(self, domain_config):
        calc = DomainRelevanceCalculator(domain_config)
        texts = ["机器学习的应用", "今天天气很好", "深度学习模型"]
        results = calc.batch_calculate(texts)
        assert len(results) == 3


# ═══════════════════════════════════════════════════════════
# CompositeWeightCalculator 测试
# ═══════════════════════════════════════════════════════════

class TestCompositeWeightCalculator:
    """复合权重计算器测试"""

    def test_init(self, domain_config):
        calc = CompositeWeightCalculator(domain_config)
        assert calc is not None

    def test_calculate_weight(self, domain_config):
        calc = CompositeWeightCalculator(domain_config)
        metadata = DocumentMetadata(
            doc_id="doc-001",
            content="机器学习是人工智能的核心",
            created_at=datetime.now() - timedelta(days=7),
            updated_at=None,
            is_evergreen=False,
            source_domain=None,
            tags=["AI"],
        )
        result = calc.calculate_weight(
            base_score=0.8,
            doc_metadata=metadata,
            query="什么是机器学习？",
        )
        assert isinstance(result, WeightedScore)
        assert result.final_score > 0

    def test_batch_calculate(self, domain_config):
        calc = CompositeWeightCalculator(domain_config)
        docs = [
            (
                0.8,
                DocumentMetadata(
                    doc_id=f"doc-{i}",
                    content=f"内容 {i}",
                    created_at=datetime.now(),
                    updated_at=None,
                    is_evergreen=False,
                    source_domain=None,
                    tags=[],
                ),
            )
            for i in range(3)
        ]
        results = calc.batch_calculate(docs, query="测试")
        assert len(results) == 3

    def test_update_factors(self, domain_config):
        calc = CompositeWeightCalculator(domain_config)
        calc.update_factors(alpha=0.5, beta=0.3, gamma=0.2)
        # 不应抛出异常
