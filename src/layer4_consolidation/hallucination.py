"""
Hallucination Detector - 幻觉检测器

基于 LLM 检测生成答案中的幻觉问题。
"""

import json
import re
from typing import List, Optional, TYPE_CHECKING

from .models import HallucinationReport
from src.core.base import BaseHallucinationDetector

if TYPE_CHECKING:
    from src.core.llm import BaseLLMClient


class HallucinationDetector(BaseHallucinationDetector):
    """
    幻觉检测器
    
    检测类型：
    1. 事实一致性 (factual_consistency): 答案是否与源文档事实一致
    2. 逻辑连贯性 (logical_coherence): 答案内部逻辑是否自洽
    3. 证据支撑度 (evidence_support): 每个声明是否有文档证据支撑
    """
    
    def __init__(
        self,
        llm_client: Optional["BaseLLMClient"] = None,
        fact_threshold: float = 0.7,
        logic_threshold: float = 0.6,
        support_threshold: float = 0.5
    ):
        """
        初始化幻觉检测器
        
        Args:
            llm_client: LLM 客户端
            fact_threshold: 事实一致性阈值
            logic_threshold: 逻辑连贯性阈值
            support_threshold: 证据支撑度阈值
        """
        self._llm_client = llm_client
        self.fact_threshold = fact_threshold
        self.logic_threshold = logic_threshold
        self.support_threshold = support_threshold
        
        # 如果没有提供 LLM 客户端，使用 Mock 实现
        if self._llm_client is None:
            try:
                from src.core.llm import MockLLMClient
                self._llm_client = MockLLMClient(model_name="mock-hallucination-detector")
            except ImportError:
                self._llm_client = None
        
        # 事实一致性检测提示词
        self._factual_prompt = """你是一个事实核查专家。请检查答案中的陈述是否与提供的证据一致。

## 待检查答案
{answer}

## 参考证据
{evidence}

## 检查要求
1. 识别答案中的每个事实性陈述
2. 检查每个陈述是否能在证据中找到支持
3. 识别任何与证据矛盾的内容

请以JSON格式返回：
```json
{{
    "score": 0.0-1.0,
    "consistent_claims": ["陈述1", "陈述2"],
    "inconsistent_claims": ["矛盾陈述1"],
    "unsupported_claims": ["无支持陈述1"],
    "analysis": "简要分析"
}}
```

请输出JSON："""
        
        # 逻辑连贯性检测提示词
        self._logic_prompt = """你是一个逻辑分析专家。请检查以下答案的内部逻辑是否连贯。

## 待检查答案
{answer}

## 检查要求
1. 检查论证链条是否完整
2. 识别逻辑跳跃或断裂
3. 检查是否存在自相矛盾

请以JSON格式返回：
```json
{{
    "score": 0.0-1.0,
    "logical_flow": true/false,
    "contradictions": ["矛盾点1"],
    "gaps": ["逻辑断裂点1"],
    "analysis": "简要分析"
}}
```

请输出JSON："""
        
        # 证据支撑度检测提示词
        self._support_prompt = """你是一个证据分析专家。请评估答案中的声明是否有充分的证据支撑。

## 待检查答案
{answer}

## 可用证据
{evidence}

## 检查要求
1. 识别答案中的所有声明
2. 为每个声明找到对应的证据支撑
3. 标记没有证据支撑的声明

请以JSON格式返回：
```json
{{
    "score": 0.0-1.0,
    "total_claims": 5,
    "supported_claims": 4,
    "unsupported_claims": ["无证据声明1"],
    "partial_support": ["部分支撑声明1"],
    "analysis": "简要分析"
}}
```

请输出JSON："""
    
    def detect(
        self,
        answer: str,
        evidence: List[str]
    ) -> HallucinationReport:
        """
        检测幻觉
        
        Args:
            answer: 答案文本
            evidence: 证据列表
            
        Returns:
            HallucinationReport: 幻觉检测报告
        """
        # 使用 LLM 进行检测
        if self._llm_client is not None:
            return self._llm_detect(answer, evidence)
        
        # 退化到规则检测
        return self._rule_based_detect(answer, evidence)
    
    def _llm_detect(
        self,
        answer: str,
        evidence: List[str]
    ) -> HallucinationReport:
        """
        使用 LLM 进行幻觉检测
        """
        # 执行三项检测
        fact_score = self._check_factual_consistency_llm(answer, evidence)
        logic_score = self._check_logical_coherence_llm(answer)
        support_score = self._check_evidence_support_llm(answer, evidence)
        
        # 判断是否存在幻觉
        is_hallucination = (
            fact_score < self.fact_threshold or
            logic_score < self.logic_threshold or
            support_score < self.support_threshold
        )
        
        # 识别问题
        issues = []
        if fact_score < self.fact_threshold:
            issues.append(f"事实一致性较低 ({fact_score:.2f})")
        if logic_score < self.logic_threshold:
            issues.append(f"逻辑连贯性不足 ({logic_score:.2f})")
        if support_score < self.support_threshold:
            issues.append(f"证据支撑度不足 ({support_score:.2f})")
        
        return HallucinationReport(
            is_hallucination=is_hallucination,
            fact_score=fact_score,
            logic_score=logic_score,
            support_score=support_score,
            issues=issues
        )
    
    def _check_factual_consistency_llm(
        self,
        answer: str,
        evidence: List[str]
    ) -> float:
        """
        使用 LLM 检查事实一致性
        """
        if not evidence:
            return 0.5  # 无证据时返回中性分数
        
        evidence_text = "\n".join([
            f"[证据{i+1}] {e}" for i, e in enumerate(evidence)
        ])
        
        prompt = self._factual_prompt.format(
            answer=answer,
            evidence=evidence_text
        )
        
        try:
            response = self._llm_client.generate(prompt, temperature=0.2)
            return self._parse_score_from_response(response, default=0.7)
        except Exception:
            return self.check_factual_consistency(answer, evidence)
    
    def _check_logical_coherence_llm(self, answer: str) -> float:
        """
        使用 LLM 检查逻辑连贯性
        """
        prompt = self._logic_prompt.format(answer=answer)
        
        try:
            response = self._llm_client.generate(prompt, temperature=0.2)
            return self._parse_score_from_response(response, default=0.7)
        except Exception:
            return self.check_logical_coherence(answer)
    
    def _check_evidence_support_llm(
        self,
        answer: str,
        evidence: List[str]
    ) -> float:
        """
        使用 LLM 检查证据支撑度
        """
        if not evidence:
            return 0.3  # 无证据时返回低分
        
        evidence_text = "\n".join([
            f"[证据{i+1}] {e}" for i, e in enumerate(evidence)
        ])
        
        prompt = self._support_prompt.format(
            answer=answer,
            evidence=evidence_text
        )
        
        try:
            response = self._llm_client.generate(prompt, temperature=0.2)
            return self._parse_score_from_response(response, default=0.6)
        except Exception:
            return self.check_evidence_support(answer, evidence)
    
    def _parse_score_from_response(
        self,
        response: str,
        default: float = 0.5
    ) -> float:
        """
        从 LLM 响应中解析分数
        """
        # 尝试提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                score = data.get("score")
                if score is not None:
                    return float(max(0.0, min(1.0, score)))
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        # 尝试从文本中提取分数
        score_patterns = [
            r'score["\s:]+(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*分',
            r'评分[：:]\s*(\d+\.?\d*)',
        ]
        
        for pattern in score_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    # 如果是百分制，转换为小数
                    if score > 1:
                        score = score / 100
                    return max(0.0, min(1.0, score))
                except ValueError:
                    pass
        
        # 基于关键词判断
        response_lower = response.lower()
        positive = sum(1 for kw in ["一致", "正确", "支持", "完整", "合理"] if kw in response_lower)
        negative = sum(1 for kw in ["矛盾", "错误", "缺乏", "不足", "幻觉"] if kw in response_lower)
        
        if positive + negative > 0:
            return 0.5 + (positive - negative) * 0.1
        
        return default
    
    def _rule_based_detect(
        self,
        answer: str,
        evidence: List[str]
    ) -> HallucinationReport:
        """
        基于规则的幻觉检测（无 LLM 时的退化方案）
        """
        fact_score = self.check_factual_consistency(answer, evidence)
        logic_score = self.check_logical_coherence(answer)
        support_score = self.check_evidence_support(answer, evidence)
        
        is_hallucination = (
            fact_score < self.fact_threshold or
            support_score < self.support_threshold
        )
        
        issues = []
        if fact_score < self.fact_threshold:
            issues.append("事实一致性较低")
        if logic_score < self.logic_threshold:
            issues.append("逻辑连贯性不足")
        if support_score < self.support_threshold:
            issues.append("证据支撑度不足")
        
        return HallucinationReport(
            is_hallucination=is_hallucination,
            fact_score=fact_score,
            logic_score=logic_score,
            support_score=support_score,
            issues=issues
        )
    
    def check_factual_consistency(
        self,
        answer: str,
        evidence: List[str]
    ) -> float:
        """
        检查事实一致性（规则方法）
        
        基于答案与证据的词汇重叠度判断
        """
        if not evidence:
            return 0.5
        
        # 提取答案和证据的关键词
        answer_words = self._extract_keywords(answer)
        evidence_words = set()
        for e in evidence:
            evidence_words.update(self._extract_keywords(e))
        
        if not answer_words:
            return 0.5
        
        # 计算重叠度
        overlap = answer_words & evidence_words
        coverage = len(overlap) / len(answer_words)
        
        # 检查是否存在明显的否定词冲突
        negation_penalty = self._check_negation_conflict(answer, evidence)
        
        return max(0.0, min(1.0, coverage - negation_penalty))
    
    def check_logical_coherence(self, answer: str) -> float:
        """
        检查逻辑连贯性（规则方法）
        
        基于答案结构和逻辑连接词判断
        """
        if len(answer) < 10:
            return 0.3
        
        score = 0.6  # 基础分
        
        # 检查逻辑连接词
        logic_connectors = [
            '因此', '所以', '但是', '然而', '因为', '由于',
            '首先', '其次', '最后', '另外', '此外',
            'therefore', 'however', 'because', 'first', 'second'
        ]
        connector_count = sum(1 for c in logic_connectors if c in answer.lower())
        score += min(connector_count * 0.05, 0.2)
        
        # 检查句子结构
        sentences = re.split(r'[。！？.!?]', answer)
        valid_sentences = [s for s in sentences if len(s.strip()) > 5]
        
        if len(valid_sentences) >= 2:
            score += 0.1
        if len(valid_sentences) >= 4:
            score += 0.1
        
        # 检查是否存在自相矛盾的表述
        contradiction_keywords = [
            ('是', '不是'), ('有', '没有'), ('能', '不能'),
            ('正确', '错误'), ('对', '错')
        ]
        
        for pos, neg in contradiction_keywords:
            if pos in answer and neg in answer:
                # 可能存在矛盾，但也可能是正常对比
                # 给予小幅惩罚
                score -= 0.05
        
        return max(0.3, min(1.0, score))
    
    def check_evidence_support(
        self,
        answer: str,
        evidence: List[str]
    ) -> float:
        """
        检查证据支撑度（规则方法）
        
        评估答案声明的证据覆盖情况
        """
        if not evidence:
            return 0.3
        
        # 将答案分解为句子/声明
        claims = re.split(r'[。！？.!?；;]', answer)
        claims = [c.strip() for c in claims if len(c.strip()) > 10]
        
        if not claims:
            return 0.5
        
        # 检查每个声明是否有证据支撑
        supported_count = 0
        
        for claim in claims:
            claim_words = self._extract_keywords(claim)
            
            for e in evidence:
                evidence_words = self._extract_keywords(e)
                
                if claim_words and evidence_words:
                    overlap = len(claim_words & evidence_words)
                    if overlap >= 2 or (overlap >= 1 and len(claim_words) <= 3):
                        supported_count += 1
                        break
        
        # 计算支撑率
        support_rate = supported_count / len(claims)
        
        # 考虑证据数量的影响
        evidence_factor = min(len(evidence) / 3, 1.0)
        
        return support_rate * 0.7 + evidence_factor * 0.3
    
    def _extract_keywords(self, text: str) -> set:
        """
        提取文本关键词
        """
        # 移除标点和停用词
        stopwords = {
            '的', '了', '是', '在', '和', '与', '或', '这', '那', '有',
            '个', '为', '上', '下', '中', '把', '被', '让', '给', '对',
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
            'to', 'of', 'in', 'for', 'on', 'with', 'as', 'at', 'by'
        }
        
        # 简单分词
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text.lower())
        
        # 过滤
        keywords = {w for w in words if len(w) >= 2 and w not in stopwords}
        
        return keywords
    
    def _check_negation_conflict(
        self,
        answer: str,
        evidence: List[str]
    ) -> float:
        """
        检查否定词冲突
        
        如果答案中的否定表述与证据冲突，返回惩罚值
        """
        negation_patterns = [
            (r'不是(.+)', r'是\1'),
            (r'没有(.+)', r'有\1'),
            (r'不能(.+)', r'能\1'),
            (r'不会(.+)', r'会\1'),
        ]
        
        penalty = 0.0
        evidence_text = ' '.join(evidence)
        
        for neg_pattern, pos_pattern in negation_patterns:
            neg_matches = re.findall(neg_pattern, answer)
            for match in neg_matches:
                # 检查证据中是否有相反的肯定表述
                pos_check = pos_pattern.replace(r'\1', re.escape(match))
                if re.search(pos_check, evidence_text):
                    penalty += 0.1
        
        return min(penalty, 0.3)
