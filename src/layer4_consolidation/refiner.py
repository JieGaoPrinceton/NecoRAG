"""
Refiner - 答案修正器

基于 Critic 反馈，通过 LLM 迭代改进答案质量。
"""

import json
import re
from typing import List, Optional, Dict, Any, TYPE_CHECKING

from .models import GeneratedAnswer, CritiqueReport
from src.core.base import BaseRefiner

if TYPE_CHECKING:
    from src.core.llm import BaseLLMClient


class Refiner(BaseRefiner):
    """
    答案修正器
    
    功能：
    - 基于 Critic 评估反馈修正答案
    - 支持多轮迭代修正
    - 融合补充证据
    """
    
    def __init__(
        self,
        llm_client: Optional["BaseLLMClient"] = None,
        max_iterations: int = 3,
        quality_threshold: float = 0.8
    ):
        """
        初始化修正器
        
        Args:
            llm_client: LLM 客户端
            max_iterations: 最大迭代次数
            quality_threshold: 质量阈值（达到则停止迭代）
        """
        self._llm_client = llm_client
        self._max_iterations = max_iterations
        self._quality_threshold = quality_threshold
        
        # 如果没有提供 LLM 客户端，使用 Mock 实现
        if self._llm_client is None:
            try:
                from src.core.llm import MockLLMClient
                self._llm_client = MockLLMClient(model_name="mock-refiner")
            except ImportError:
                self._llm_client = None
        
        # 修正提示词模板
        self._refine_prompt = """你是一个专业的答案修正专家。请根据评估反馈改进答案。

## 原始问题
{query}

## 当前答案
{answer}

## 评估反馈
质量评分：{quality_score:.2f}
发现的问题：
{issues}

改进建议：
{suggestions}

## 可用证据
{evidence}

## 修正要求
1. 针对发现的问题进行修正
2. 确保答案与证据一致
3. 保持答案的完整性和相关性
4. 使用清晰、专业的语言

请输出修正后的答案（直接输出答案内容，不要包含任何解释）："""
        
        # 融合证据的提示词
        self._evidence_integration_prompt = """请将以下补充证据融入到答案中：

当前答案：
{answer}

补充证据：
{additional_evidence}

要求：
1. 自然地融入新证据，不要简单拼接
2. 保持答案的连贯性
3. 如果新证据与原答案矛盾，优先采用新证据

请输出修改后的答案："""
    
    def refine(
        self,
        answer: GeneratedAnswer,
        critique: CritiqueReport,
        additional_evidence: Optional[List[str]] = None,
        query: Optional[str] = None,
        original_evidence: Optional[List[str]] = None
    ) -> GeneratedAnswer:
        """
        根据批判修正答案
        
        Args:
            answer: 原始答案
            critique: 批判报告
            additional_evidence: 补充证据
            query: 原始查询
            original_evidence: 原始证据
            
        Returns:
            GeneratedAnswer: 修正后的答案
        """
        # 如果质量已达标，直接返回
        if critique.quality_score >= self._quality_threshold and not critique.issues:
            return answer
        
        # 使用 LLM 进行修正
        if self._llm_client is not None:
            return self._llm_refine(
                answer, critique, additional_evidence, query, original_evidence
            )
        
        # 退化到规则修正
        return self._rule_based_refine(answer, critique, additional_evidence)
    
    def refine_iterative(
        self,
        answer: GeneratedAnswer,
        critique_func,
        evidence: List[str],
        query: Optional[str] = None
    ) -> GeneratedAnswer:
        """
        迭代修正答案直到质量达标或达到最大迭代次数
        
        Args:
            answer: 原始答案
            critique_func: 批判函数（接收 answer 和 evidence，返回 CritiqueReport）
            evidence: 证据列表
            query: 原始查询
            
        Returns:
            GeneratedAnswer: 最终修正后的答案
        """
        current_answer = answer
        iteration = 0
        
        while iteration < self._max_iterations:
            # 评估当前答案
            critique = critique_func(current_answer, evidence)
            
            # 检查是否达标
            if critique.quality_score >= self._quality_threshold and not critique.issues:
                break
            
            # 修正答案
            current_answer = self.refine(
                current_answer,
                critique,
                query=query,
                original_evidence=evidence
            )
            
            # 更新迭代信息
            current_answer.metadata["iteration"] = iteration + 1
            iteration += 1
        
        current_answer.metadata["total_iterations"] = iteration
        return current_answer
    
    def _llm_refine(
        self,
        answer: GeneratedAnswer,
        critique: CritiqueReport,
        additional_evidence: Optional[List[str]] = None,
        query: Optional[str] = None,
        original_evidence: Optional[List[str]] = None
    ) -> GeneratedAnswer:
        """
        使用 LLM 修正答案
        """
        # 格式化问题和建议
        issues_text = "\n".join([f"- {issue}" for issue in critique.issues]) or "无明显问题"
        suggestions_text = "\n".join([f"- {s}" for s in critique.suggestions]) or "无具体建议"
        
        # 合并证据
        all_evidence = list(original_evidence or [])
        if additional_evidence:
            all_evidence.extend(additional_evidence)
        
        evidence_text = "\n".join([
            f"[证据{i+1}] {e}" for i, e in enumerate(all_evidence)
        ]) if all_evidence else "（无可用证据）"
        
        # 构建提示词
        prompt = self._refine_prompt.format(
            query=query or "（未提供原始问题）",
            answer=answer.content,
            quality_score=critique.quality_score,
            issues=issues_text,
            suggestions=suggestions_text,
            evidence=evidence_text
        )
        
        # 调用 LLM
        try:
            refined_content = self._llm_client.generate(prompt, temperature=0.5)
            
            # 清理响应（移除可能的格式标记）
            refined_content = self._clean_response(refined_content)
            
            # 计算新的置信度
            # 基于原置信度和批判评分调整
            new_confidence = self._calculate_refined_confidence(
                answer.confidence, critique.quality_score
            )
            
            # 更新引用
            new_citations = list(answer.citations)
            if additional_evidence:
                new_citations.extend([
                    f"additional_{i}" for i in range(len(additional_evidence))
                ])
            
            return GeneratedAnswer(
                content=refined_content,
                citations=new_citations,
                confidence=new_confidence,
                metadata={
                    "refined": True,
                    "original_quality_score": critique.quality_score,
                    "critique_issues": len(critique.issues),
                    "refinement_method": "llm"
                }
            )
        except Exception as e:
            # LLM 调用失败，退化到规则修正
            return self._rule_based_refine(answer, critique, additional_evidence)
    
    def _rule_based_refine(
        self,
        answer: GeneratedAnswer,
        critique: CritiqueReport,
        additional_evidence: Optional[List[str]] = None
    ) -> GeneratedAnswer:
        """
        基于规则修正答案（无 LLM 时的退化方案）
        """
        refined_content = answer.content
        
        # 1. 处理答案过短的问题
        if "过于简短" in str(critique.issues):
            refined_content = self._expand_answer(refined_content)
        
        # 2. 融合补充证据
        if additional_evidence:
            evidence_summary = self._summarize_evidence(additional_evidence)
            if evidence_summary:
                refined_content = f"{refined_content}\n\n补充信息：{evidence_summary}"
        
        # 3. 处理证据关联度低的问题
        if "关联度" in str(critique.issues) and additional_evidence:
            # 尝试从补充证据中提取关键信息
            key_points = self._extract_key_points(additional_evidence)
            if key_points:
                refined_content = f"{refined_content}\n\n相关要点：\n{key_points}"
        
        # 计算新置信度
        new_confidence = self._calculate_refined_confidence(
            answer.confidence, critique.quality_score
        )
        
        # 更新引用
        new_citations = list(answer.citations)
        if additional_evidence:
            new_citations.extend([
                f"additional_{i}" for i in range(len(additional_evidence))
            ])
        
        return GeneratedAnswer(
            content=refined_content,
            citations=new_citations,
            confidence=new_confidence,
            metadata={
                "refined": True,
                "original_quality_score": critique.quality_score,
                "critique_issues": len(critique.issues),
                "refinement_method": "rule_based"
            }
        )
    
    def _clean_response(self, response: str) -> str:
        """
        清理 LLM 响应
        """
        # 移除可能的代码块标记
        response = re.sub(r'^```[\w]*\n?', '', response)
        response = re.sub(r'\n?```$', '', response)
        
        # 移除开头的解释性文字
        lines = response.strip().split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if line.strip() and not line.startswith(('以下是', '修正后', '答案：', '输出：')):
                start_idx = i
                break
        
        return '\n'.join(lines[start_idx:]).strip()
    
    def _calculate_refined_confidence(
        self,
        original_confidence: float,
        quality_score: float
    ) -> float:
        """
        计算修正后的置信度
        """
        # 如果质量评分较高，提升置信度
        if quality_score >= 0.7:
            adjustment = (quality_score - 0.7) * 0.3
            return min(original_confidence + adjustment, 0.95)
        else:
            # 质量评分较低，但经过修正应该有所提升
            return min(original_confidence + 0.05, 0.8)
    
    def _expand_answer(self, content: str) -> str:
        """
        扩展过短的答案
        """
        if len(content) < 50:
            return f"关于这个问题，{content}\n\n如需了解更多详细信息，请提供更具体的问题描述。"
        return content
    
    def _summarize_evidence(self, evidence: List[str]) -> str:
        """
        简要总结证据
        """
        if not evidence:
            return ""
        
        summaries = []
        for e in evidence[:3]:  # 最多处理3条
            # 截取前150个字符
            summary = e[:150].strip()
            if len(e) > 150:
                summary += "..."
            summaries.append(summary)
        
        return " ".join(summaries)
    
    def _extract_key_points(self, evidence: List[str]) -> str:
        """
        从证据中提取关键要点
        """
        if not evidence:
            return ""
        
        points = []
        for i, e in enumerate(evidence[:3], 1):
            # 提取第一句话作为要点
            first_sentence = e.split('。')[0] if '。' in e else e[:100]
            points.append(f"{i}. {first_sentence.strip()}")
        
        return "\n".join(points)
