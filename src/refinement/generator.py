"""
Generator - 答案生成器

基于检索证据生成高质量答案，支持 LLM 客户端依赖注入。
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING

from src.refinement.models import GeneratedAnswer

if TYPE_CHECKING:
    from src.core.llm import BaseLLMClient


class Generator:
    """
    答案生成器
    
    基于检索证据生成答案，支持：
    - LLM 客户端依赖注入
    - 多种生成策略
    - 置信度评估
    """
    
    def __init__(
        self,
        llm_client: Optional["BaseLLMClient"] = None,
        max_evidence: int = 5,
        temperature: float = 0.7
    ):
        """
        初始化生成器
        
        Args:
            llm_client: LLM 客户端
            max_evidence: 最大使用证据数量
            temperature: 生成温度
        """
        self._llm_client = llm_client
        self._max_evidence = max_evidence
        self._temperature = temperature
        
        # 如果没有提供 LLM 客户端，使用 Mock 实现
        if self._llm_client is None:
            try:
                from src.core.llm import MockLLMClient
                self._llm_client = MockLLMClient(model_name="mock-generator")
            except ImportError:
                self._llm_client = None
        
        # 生成提示词模板
        self._generation_prompt = """你是一个专业的问答助手。请根据提供的证据回答用户的问题。

要求：
1. 答案必须基于提供的证据
2. 如果证据不足以回答问题，请明确说明
3. 使用清晰、专业的语言
4. 在答案中引用相关证据

证据：
{evidence}

问题：{query}

请提供详细的答案："""
    
    def generate(
        self,
        query: str,
        evidence: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> GeneratedAnswer:
        """
        基于证据生成答案
        
        Args:
            query: 查询文本
            evidence: 证据列表
            context: 上下文信息
            
        Returns:
            GeneratedAnswer: 生成的答案
        """
        # 处理无证据情况
        if not evidence:
            return GeneratedAnswer(
                content="抱歉，我无法找到与您问题相关的信息。请尝试用不同的方式描述您的问题。",
                citations=[],
                confidence=0.0
            )
        
        # 选择证据（限制数量）
        selected_evidence = evidence[:self._max_evidence]
        
        # 使用 LLM 生成答案
        if self._llm_client is not None:
            return self._llm_generate(query, selected_evidence, context)
        
        # 回退到规则生成
        return self._rule_based_generate(query, selected_evidence, context)
    
    def _llm_generate(
        self,
        query: str,
        evidence: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> GeneratedAnswer:
        """
        使用 LLM 生成答案
        """
        # 格式化证据
        evidence_text = "\n\n".join([
            f"[证据{i+1}] {e}" for i, e in enumerate(evidence)
        ])
        
        # 构建提示词
        prompt = self._generation_prompt.format(
            evidence=evidence_text,
            query=query
        )
        
        # 添加上下文信息
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            prompt = f"上下文信息：\n{context_str}\n\n{prompt}"
        
        # 调用 LLM
        content = self._llm_client.generate(
            prompt,
            temperature=self._temperature
        )
        
        # 评估置信度
        confidence = self._estimate_confidence(query, evidence, content)
        
        return GeneratedAnswer(
            content=content,
            citations=[f"evidence_{i}" for i in range(len(evidence))],
            confidence=confidence
        )
    
    def _rule_based_generate(
        self,
        query: str,
        evidence: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> GeneratedAnswer:
        """
        基于规则生成答案（回退方案）
        """
        # 构建答案结构
        parts = [
            f"根据检索到的信息，针对「{query}」的回答如下：",
            ""
        ]
        
        for i, e in enumerate(evidence):
            # 截取证据片段
            snippet = e[:300] + "..." if len(e) > 300 else e
            parts.append(f"**要点 {i+1}**：{snippet}")
            parts.append("")
        
        parts.append("以上信息来自知识库的相关文档，仅供参考。")
        
        content = "\n".join(parts)
        
        # 基于证据数量估算置信度
        confidence = min(0.9, 0.5 + len(evidence) * 0.1)
        
        return GeneratedAnswer(
            content=content,
            citations=[f"evidence_{i}" for i in range(len(evidence))],
            confidence=confidence
        )
    
    def _estimate_confidence(
        self,
        query: str,
        evidence: List[str],
        answer: str
    ) -> float:
        """
        估算答案置信度
        
        基于多个因素：证据数量、答案长度、关键词覆盖
        """
        confidence = 0.5
        
        # 证据数量因素
        evidence_factor = min(len(evidence) / 3, 1.0) * 0.2
        confidence += evidence_factor
        
        # 答案长度因素（太短或太长都不好）
        answer_len = len(answer)
        if 100 <= answer_len <= 500:
            confidence += 0.15
        elif 50 <= answer_len <= 800:
            confidence += 0.1
        
        # 关键词覆盖因素
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        if query_words:
            coverage = len(query_words & answer_words) / len(query_words)
            confidence += coverage * 0.15
        
        return min(confidence, 0.95)
