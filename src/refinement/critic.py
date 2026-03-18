"""
Critic - 批判评估器

基于 LLM 对生成答案进行多维度质量评估。
"""

import json
import re
from typing import List, Optional, Dict, Any, TYPE_CHECKING

from src.refinement.models import GeneratedAnswer, CritiqueReport
from src.core.base import BaseCritic

if TYPE_CHECKING:
    from src.core.llm import BaseLLMClient


class Critic(BaseCritic):
    """
    批判评估器
    
    评估维度：
    - 事实性 (factuality): 答案是否与证据事实一致
    - 完整性 (completeness): 答案是否完整回答了问题
    - 相关性 (relevance): 答案与问题的相关程度
    """
    
    def __init__(
        self,
        llm_client: Optional["BaseLLMClient"] = None,
        factuality_weight: float = 0.4,
        completeness_weight: float = 0.3,
        relevance_weight: float = 0.3
    ):
        """
        初始化批判器
        
        Args:
            llm_client: LLM 客户端
            factuality_weight: 事实性权重
            completeness_weight: 完整性权重
            relevance_weight: 相关性权重
        """
        self._llm_client = llm_client
        self._factuality_weight = factuality_weight
        self._completeness_weight = completeness_weight
        self._relevance_weight = relevance_weight
        
        # 如果没有提供 LLM 客户端，使用 Mock 实现
        if self._llm_client is None:
            try:
                from src.core.llm import MockLLMClient
                self._llm_client = MockLLMClient(model_name="mock-critic")
            except ImportError:
                self._llm_client = None
        
        # 评估提示词模板
        self._critique_prompt = """你是一个专业的答案质量评估专家。请对以下答案进行多维度评估。

## 评估维度
1. 事实性 (factuality): 答案中的陈述是否与提供的证据一致，有无错误或矛盾
2. 完整性 (completeness): 答案是否完整回答了用户的问题，有无遗漏关键信息
3. 相关性 (relevance): 答案内容与问题的相关程度，有无跑题或冗余内容

## 待评估内容
问题：{query}

答案：{answer}

证据：
{evidence}

## 输出格式
请以JSON格式返回评估结果：
```json
{{
    "factuality_score": 0.0-1.0,
    "factuality_issues": ["问题1", "问题2"],
    "completeness_score": 0.0-1.0,
    "completeness_issues": ["问题1"],
    "relevance_score": 0.0-1.0,
    "relevance_issues": [],
    "suggestions": ["建议1", "建议2"],
    "summary": "总体评价"
}}
```

请严格按照JSON格式输出："""
    
    def critique(
        self,
        answer: GeneratedAnswer,
        evidence: List[str],
        query: Optional[str] = None
    ) -> CritiqueReport:
        """
        评估答案质量
        
        Args:
            answer: 生成的答案
            evidence: 证据列表
            query: 原始查询（可选）
            
        Returns:
            CritiqueReport: 批判报告
        """
        # 使用 LLM 进行评估
        if self._llm_client is not None:
            return self._llm_critique(answer, evidence, query)
        
        # 退化到规则评估
        return self._rule_based_critique(answer, evidence)
    
    def _llm_critique(
        self,
        answer: GeneratedAnswer,
        evidence: List[str],
        query: Optional[str] = None
    ) -> CritiqueReport:
        """
        使用 LLM 进行评估
        """
        # 格式化证据
        evidence_text = "\n".join([
            f"[证据{i+1}] {e}" for i, e in enumerate(evidence)
        ]) if evidence else "（无可用证据）"
        
        # 构建提示词
        prompt = self._critique_prompt.format(
            query=query or "（未提供原始问题）",
            answer=answer.content,
            evidence=evidence_text
        )
        
        # 调用 LLM
        try:
            response = self._llm_client.generate(prompt, temperature=0.3)
            return self._parse_critique_response(response, answer, evidence)
        except Exception as e:
            # LLM 调用失败，退化到规则评估
            return self._rule_based_critique(answer, evidence)
    
    def _parse_critique_response(
        self,
        response: str,
        answer: GeneratedAnswer,
        evidence: List[str]
    ) -> CritiqueReport:
        """
        解析 LLM 评估响应
        """
        # 尝试提取 JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        
        if json_match:
            try:
                data = json.loads(json_match.group())
                
                # 提取评分
                factuality = float(data.get("factuality_score", 0.7))
                completeness = float(data.get("completeness_score", 0.7))
                relevance = float(data.get("relevance_score", 0.7))
                
                # 计算加权总分
                quality_score = (
                    factuality * self._factuality_weight +
                    completeness * self._completeness_weight +
                    relevance * self._relevance_weight
                )
                
                # 收集所有问题
                issues = []
                issues.extend(data.get("factuality_issues", []))
                issues.extend(data.get("completeness_issues", []))
                issues.extend(data.get("relevance_issues", []))
                
                # 获取建议
                suggestions = data.get("suggestions", [])
                if not suggestions and data.get("summary"):
                    suggestions = [data["summary"]]
                
                return CritiqueReport(
                    is_valid=quality_score >= 0.6 and len(issues) <= 2,
                    issues=issues,
                    suggestions=suggestions,
                    quality_score=quality_score
                )
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        
        # JSON 解析失败，基于响应内容做简单判断
        return self._fallback_parse(response, answer, evidence)
    
    def _fallback_parse(
        self,
        response: str,
        answer: GeneratedAnswer,
        evidence: List[str]
    ) -> CritiqueReport:
        """
        回退解析：基于响应内容关键词判断
        """
        response_lower = response.lower()
        
        # 关键词检测
        positive_keywords = ["正确", "准确", "完整", "相关", "good", "correct", "accurate"]
        negative_keywords = ["错误", "不准确", "缺失", "遗漏", "不相关", "error", "incorrect", "missing"]
        
        positive_count = sum(1 for kw in positive_keywords if kw in response_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in response_lower)
        
        # 基于关键词计算分数
        if positive_count + negative_count > 0:
            quality_score = positive_count / (positive_count + negative_count)
        else:
            quality_score = 0.7  # 默认分数
        
        issues = []
        suggestions = []
        
        if negative_count > positive_count:
            issues.append("答案可能存在质量问题")
            suggestions.append("建议根据证据重新审核答案")
        
        return CritiqueReport(
            is_valid=quality_score >= 0.6,
            issues=issues,
            suggestions=suggestions,
            quality_score=quality_score
        )
    
    def _rule_based_critique(
        self,
        answer: GeneratedAnswer,
        evidence: List[str]
    ) -> CritiqueReport:
        """
        基于规则的评估（无 LLM 时的退化方案）
        
        评估逻辑：
        - 检查证据引用
        - 检查置信度
        - 检查答案长度和结构
        """
        issues = []
        suggestions = []
        scores = {
            "factuality": 0.8,
            "completeness": 0.8,
            "relevance": 0.8
        }
        
        # 1. 检查证据引用
        if not answer.citations:
            issues.append("答案缺乏证据引用")
            suggestions.append("建议在答案中引用相关证据")
            scores["factuality"] -= 0.2
        
        # 2. 检查置信度
        if answer.confidence < 0.5:
            issues.append("答案置信度过低")
            suggestions.append("建议补充更多证据提高置信度")
            scores["completeness"] -= 0.2
        elif answer.confidence < 0.3:
            scores["completeness"] -= 0.3
        
        # 3. 检查答案长度
        content_len = len(answer.content)
        if content_len < 20:
            issues.append("答案过于简短")
            suggestions.append("建议提供更详细的回答")
            scores["completeness"] -= 0.3
        elif content_len < 50:
            scores["completeness"] -= 0.1
        
        # 4. 检查与证据的关键词重叠
        if evidence:
            answer_words = set(answer.content.lower().split())
            evidence_words = set()
            for e in evidence:
                evidence_words.update(e.lower().split())
            
            if answer_words:
                overlap_ratio = len(answer_words & evidence_words) / len(answer_words)
                if overlap_ratio < 0.1:
                    issues.append("答案与证据关联度较低")
                    suggestions.append("建议更紧密地基于证据作答")
                    scores["relevance"] -= 0.2
                elif overlap_ratio < 0.2:
                    scores["relevance"] -= 0.1
        else:
            issues.append("缺少可用证据进行验证")
            scores["factuality"] -= 0.2
        
        # 计算加权总分
        quality_score = (
            scores["factuality"] * self._factuality_weight +
            scores["completeness"] * self._completeness_weight +
            scores["relevance"] * self._relevance_weight
        )
        quality_score = max(0.0, min(1.0, quality_score))
        
        return CritiqueReport(
            is_valid=len(issues) == 0,
            issues=issues,
            suggestions=suggestions,
            quality_score=quality_score
        )
