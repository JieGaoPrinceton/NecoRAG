"""
HyDE Enhancer - HyDE 增强器
Hypothetical Document Embeddings

通过生成假设性答案来增强检索效果：
1. LLM 生成假设答案
2. 假设答案向量化
3. 用假设答案向量检索真实文档
"""

from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.llm import BaseLLMClient


class HyDEEnhancer:
    """
    HyDE 增强器
    
    解决提问模糊问题，通过生成假设性文档来优化检索。
    """
    
    def __init__(
        self,
        llm_client: Optional["BaseLLMClient"] = None,
        temperature: float = 0.5,
        num_hypotheses: int = 1
    ):
        """
        初始化 HyDE 增强器
        
        Args:
            llm_client: LLM 客户端（用于生成假设答案）
            temperature: 生成温度
            num_hypotheses: 生成假设数量
        """
        self._llm_client = llm_client
        self._temperature = temperature
        self._num_hypotheses = num_hypotheses
        
        # 如果没有提供 LLM 客户端，使用 Mock 实现
        if self._llm_client is None:
            try:
                from src.core.llm import MockLLMClient
                self._llm_client = MockLLMClient(model_name="mock-hyde")
            except ImportError:
                self._llm_client = None
        
        # 提示词模板
        self._hypothesis_prompt = """请为以下问题生成一个假设性的答案文档。
这个答案应该模拟一个包含答案的真实文档的内容风格。

问题：{query}

请生成一个简洁但信息丰富的假设性答案（100-200字）："""
    
    def generate_hypothetical_doc(
        self,
        query: str,
        max_length: int = 300
    ) -> str:
        """
        生成假设文档
        
        Args:
            query: 查询文本
            max_length: 最大长度
            
        Returns:
            str: 假设文档内容
        """
        if self._llm_client is not None:
            prompt = self._hypothesis_prompt.format(query=query)
            hypothesis = self._llm_client.generate(
                prompt,
                max_tokens=max_length,
                temperature=self._temperature
            )
            return hypothesis
        
        # 回退到规则生成
        return self._rule_based_hypothesis(query, max_length)
    
    def generate_multiple_hypotheses(
        self,
        query: str,
        num_hypotheses: Optional[int] = None,
        max_length: int = 300
    ) -> List[str]:
        """
        生成多个假设文档
        
        Args:
            query: 查询文本
            num_hypotheses: 假设数量
            max_length: 单个假设最大长度
            
        Returns:
            List[str]: 假设文档列表
        """
        n = num_hypotheses or self._num_hypotheses
        hypotheses = []
        
        for i in range(n):
            # 通过调整温度生成多样化的假设
            temp = self._temperature + (i * 0.1)
            
            if self._llm_client is not None:
                prompt = self._hypothesis_prompt.format(query=query)
                hypothesis = self._llm_client.generate(
                    prompt,
                    max_tokens=max_length,
                    temperature=min(temp, 1.0)
                )
            else:
                hypothesis = self._rule_based_hypothesis(query, max_length, variation=i)
            
            hypotheses.append(hypothesis)
        
        return hypotheses
    
    def get_hypothesis_embedding(
        self,
        query: str,
        max_length: int = 300
    ) -> Optional[List[float]]:
        """
        获取假设文档的向量表示
        
        Args:
            query: 查询文本
            max_length: 假设文档最大长度
            
        Returns:
            Optional[List[float]]: 假设文档向量
        """
        if self._llm_client is None:
            return None
        
        hypothesis = self.generate_hypothetical_doc(query, max_length)
        return self._llm_client.embed(hypothesis)
    
    def enhance_query(
        self,
        query: str,
        include_original: bool = True
    ) -> List[str]:
        """
        增强查询
        
        生成包含原始查询和假设文档的查询列表。
        
        Args:
            query: 原始查询
            include_original: 是否包含原始查询
            
        Returns:
            List[str]: 增强后的查询列表
        """
        queries = []
        
        if include_original:
            queries.append(query)
        
        # 添加假设文档
        hypotheses = self.generate_multiple_hypotheses(query)
        queries.extend(hypotheses)
        
        return queries
    
    def _rule_based_hypothesis(
        self,
        query: str,
        max_length: int = 300,
        variation: int = 0
    ) -> str:
        """
        基于规则生成假设文档（回退方案）
        
        Args:
            query: 查询文本
            max_length: 最大长度
            variation: 变体编号
            
        Returns:
            str: 假设文档
        """
        templates = [
            "关于「{query}」，以下是相关的详细说明：\n\n"
            "{query}是一个重要的概念。在实际应用中，它涉及多个方面的考虑。"
            "首先，需要理解其基本原理；其次，要掌握相关的实践方法；"
            "最后，还需要了解常见的应用场景和注意事项。",
            
            "针对「{query}」这个问题，可以从以下几个角度来分析：\n\n"
            "1. 基本概念：{query}的定义和范围\n"
            "2. 核心要点：关键的技术或方法论\n"
            "3. 实践应用：具体的使用场景和案例",
            
            "{query}相关内容概述：\n\n"
            "这是一个涵盖多个领域的主题。从理论角度看，"
            "它建立在特定的基础知识之上；从实践角度看，"
            "它需要结合具体场景进行应用和调整。"
        ]
        
        template = templates[variation % len(templates)]
        hypothesis = template.format(query=query)
        
        if len(hypothesis) > max_length:
            hypothesis = hypothesis[:max_length]
        
        return hypothesis
