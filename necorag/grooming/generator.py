"""
Generator - 答案生成器
"""

from typing import List, Dict, Any
from necorag.grooming.models import GeneratedAnswer


class Generator:
    """
    答案生成器
    
    基于检索证据生成答案
    """
    
    def __init__(self, llm_model: str = "default"):
        """
        初始化生成器
        
        Args:
            llm_model: LLM 模型名称
        """
        self.llm_model = llm_model
    
    def generate(
        self,
        query: str,
        evidence: List[str],
        context: Dict[str, Any] = None
    ) -> GeneratedAnswer:
        """
        基于证据生成答案
        
        Args:
            query: 查询文本
            evidence: 证据列表
            context: 上下文信息
            
        Returns:
            GeneratedAnswer: 生成的答案
            
        TODO: 集成 LLM 生成
        """
        # 最小实现：简单拼接证据
        if not evidence:
            return GeneratedAnswer(
                content="抱歉，我无法找到相关信息。",
                citations=[],
                confidence=0.0
            )
        
        # 简单答案生成
        answer_parts = []
        for i, e in enumerate(evidence[:3]):  # 最多使用 3 条证据
            answer_parts.append(f"[{i+1}] {e[:200]}")
        
        content = f"根据检索到的信息：\n\n" + "\n\n".join(answer_parts)
        
        return GeneratedAnswer(
            content=content,
            citations=[f"evidence_{i}" for i in range(min(len(evidence), 3))],
            confidence=0.7 if evidence else 0.0
        )
