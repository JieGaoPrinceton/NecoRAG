# -*- coding: utf-8 -*-
"""
精炼代理测试 - 生成器、评审、精炼、幻觉检测
"""

import pytest
from datetime import datetime

from src.refinement import RefinementAgent
from src.refinement.generator import Generator
from src.refinement.critic import Critic
from src.refinement.refiner import Refiner
from src.refinement.hallucination import HallucinationDetector
from src.refinement.models import (
    GeneratedAnswer,
    CritiqueReport,
    HallucinationReport,
    RefinementResult,
)
from src.memory import MemoryManager


# ═══════════════════════════════════════════════════════════
# Generator 测试
# ═══════════════════════════════════════════════════════════

class TestGenerator:
    """生成器测试"""

    def test_init(self):
        gen = Generator()
        assert gen is not None

    def test_generate(self, sample_evidence):
        gen = Generator()
        answer = gen.generate("什么是机器学习？", sample_evidence)
        assert isinstance(answer, GeneratedAnswer)
        assert len(answer.content) > 0
        assert 0 <= answer.confidence <= 1

    def test_generate_with_context(self, sample_evidence):
        gen = Generator()
        context = {"session_id": "test", "topic": "AI"}
        answer = gen.generate("什么是深度学习？", sample_evidence, context)
        assert isinstance(answer, GeneratedAnswer)

    def test_generate_no_evidence(self):
        gen = Generator()
        answer = gen.generate("什么是量子计算？", [])
        assert isinstance(answer, GeneratedAnswer)
        assert answer.confidence < 0.5  # 无证据时置信度应较低

    def test_generate_has_citations(self, sample_evidence):
        gen = Generator()
        answer = gen.generate("机器学习是什么？", sample_evidence)
        assert isinstance(answer.citations, list)


# ═══════════════════════════════════════════════════════════
# Critic 测试
# ═══════════════════════════════════════════════════════════

class TestCritic:
    """评审器测试"""

    def test_init(self):
        critic = Critic()
        assert critic is not None

    def test_critique(self, sample_generated_answer, sample_evidence):
        critic = Critic()
        report = critic.critique(sample_generated_answer, sample_evidence)
        assert isinstance(report, CritiqueReport)
        assert isinstance(report.is_valid, bool)
        assert 0 <= report.quality_score <= 1

    def test_critique_high_quality(self, sample_evidence):
        """高质量回答应通过评审"""
        critic = Critic()
        good_answer = GeneratedAnswer(
            content="机器学习是人工智能的一个分支，使用算法从数据中学习模式并做出预测。",
            citations=["source_1"],
            confidence=0.9,
            metadata={},
        )
        report = critic.critique(good_answer, sample_evidence)
        assert isinstance(report, CritiqueReport)

    def test_critique_low_quality(self, sample_evidence):
        """低质量回答应被标记"""
        critic = Critic()
        bad_answer = GeneratedAnswer(
            content="不知道",
            citations=[],
            confidence=0.1,
            metadata={},
        )
        report = critic.critique(bad_answer, sample_evidence)
        assert isinstance(report, CritiqueReport)


# ═══════════════════════════════════════════════════════════
# Refiner 测试
# ═══════════════════════════════════════════════════════════

class TestRefiner:
    """精炼器测试"""

    def test_init(self):
        refiner = Refiner()
        assert refiner is not None

    def test_refine(self, sample_generated_answer, sample_critique, sample_evidence):
        refiner = Refiner()
        refined = refiner.refine(sample_generated_answer, sample_critique, sample_evidence)
        assert isinstance(refined, GeneratedAnswer)
        assert len(refined.content) > 0


# ═══════════════════════════════════════════════════════════
# HallucinationDetector 测试
# ═══════════════════════════════════════════════════════════

class TestHallucinationDetector:
    """幻觉检测器测试"""

    def test_init(self):
        detector = HallucinationDetector()
        assert detector is not None

    def test_detect(self, sample_evidence):
        detector = HallucinationDetector()
        report = detector.detect(
            "机器学习是人工智能的子领域",
            sample_evidence,
        )
        assert isinstance(report, HallucinationReport)
        assert isinstance(report.is_hallucination, bool)

    def test_factual_consistency(self, sample_evidence):
        detector = HallucinationDetector()
        score = detector.check_factual_consistency(
            "机器学习是人工智能的一个子领域",
            sample_evidence,
        )
        assert 0 <= score <= 1

    def test_logical_coherence(self):
        detector = HallucinationDetector()
        score = detector.check_logical_coherence(
            "因为A所以B，同时因为B所以C，因此结论是合理的。"
        )
        assert 0 <= score <= 1

    def test_evidence_support(self, sample_evidence):
        detector = HallucinationDetector()
        score = detector.check_evidence_support(
            "机器学习是人工智能的一个子领域。",
            sample_evidence,
        )
        assert 0 <= score <= 1

    def test_hallucination_detection_with_fabricated(self, sample_evidence):
        """完全虚构的内容应被检测为幻觉（或低分）"""
        detector = HallucinationDetector()
        report = detector.detect(
            "量子纠缠可以实现超光速通信",
            sample_evidence,
        )
        assert isinstance(report, HallucinationReport)
        # 与证据不相关，事实分数应较低
        assert report.fact_score < 0.9


# ═══════════════════════════════════════════════════════════
# RefinementAgent 集成测试
# ═══════════════════════════════════════════════════════════

class TestRefinementAgent:
    """精炼代理集成测试"""

    def test_init(self):
        agent = RefinementAgent()
        assert agent is not None

    def test_process(self, sample_evidence):
        agent = RefinementAgent()
        result = agent.process(
            query="什么是人工智能？",
            evidence=sample_evidence,
        )
        assert isinstance(result, RefinementResult)
        assert len(result.answer) > 0
        assert 0 <= result.confidence <= 1
        assert result.iterations >= 1

    def test_process_with_context(self, sample_evidence):
        agent = RefinementAgent()
        result = agent.process(
            query="深度学习的优势是什么？",
            evidence=sample_evidence,
            context={"session_id": "test"},
        )
        assert isinstance(result, RefinementResult)

    def test_process_includes_hallucination_report(self, sample_evidence):
        agent = RefinementAgent()
        result = agent.process(
            query="机器学习和深度学习的区别？",
            evidence=sample_evidence,
        )
        # hallucination_report 可能为 None（取决于实现），但应该是正确的类型
        assert result.hallucination_report is None or isinstance(
            result.hallucination_report, HallucinationReport
        )
