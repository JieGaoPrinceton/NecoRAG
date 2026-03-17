"""
Grooming Agent - 梳理代理主类
"""

from typing import List, Optional
from necorag.memory.manager import MemoryManager
from necorag.grooming.generator import Generator
from necorag.grooming.critic import Critic
from necorag.grooming.refiner import Refiner
from necorag.grooming.hallucination import HallucinationDetector
from necorag.grooming.consolidator import KnowledgeConsolidator
from necorag.grooming.pruner import MemoryPruner
from necorag.grooming.models import GroomingResult, HallucinationReport


class GroomingAgent:
    """
    梳理代理
    
    功能：
    - Generator -> Critic -> Refiner 闭环
    - 幻觉自检
    - 异步知识固化
    - 记忆修剪
    """
    
    def __init__(
        self,
        llm_model: str = "default",
        memory: MemoryManager = None,
        max_iterations: int = 3,
        min_confidence: float = 0.7
    ):
        """
        初始化梳理代理
        
        Args:
            llm_model: LLM 模型
            memory: 记忆管理器
            max_iterations: 最大迭代次数
            min_confidence: 最低置信度
        """
        self.llm_model = llm_model
        self.memory = memory
        self.max_iterations = max_iterations
        self.min_confidence = min_confidence
        
        # 初始化子组件
        self.generator = Generator(llm_model)
        self.critic = Critic(llm_model)
        self.refiner = Refiner(llm_model)
        self.hallucination_detector = HallucinationDetector()
        
        if memory:
            self.consolidator = KnowledgeConsolidator(memory)
            self.pruner = MemoryPruner(memory)
        else:
            self.consolidator = None
            self.pruner = None
    
    def process(
        self,
        query: str,
        evidence: List[str],
        context: dict = None
    ) -> GroomingResult:
        """
        处理查询，生成并验证答案
        
        Args:
            query: 查询文本
            evidence: 证据列表
            context: 上下文
            
        Returns:
            GroomingResult: 梳理结果
        """
        iteration = 0
        current_evidence = evidence.copy()
        
        # 生成初始答案
        answer = self.generator.generate(query, current_evidence, context)
        
        while iteration < self.max_iterations:
            iteration += 1
            
            # 批判评估
            critique = self.critic.critique(answer, current_evidence)
            
            # 幻觉检测
            hallucination_report = self.hallucination_detector.detect(
                answer.content,
                current_evidence
            )
            
            # 检查是否通过
            if critique.is_valid and not hallucination_report.is_hallucination:
                # 通过验证，返回结果
                return GroomingResult(
                    query=query,
                    answer=answer.content,
                    confidence=answer.confidence,
                    citations=answer.citations,
                    hallucination_report=hallucination_report,
                    iterations=iteration
                )
            
            # 未通过，修正答案
            if not critique.is_valid:
                answer = self.refiner.refine(
                    answer,
                    critique,
                    additional_evidence=None
                )
            
            # 如果检测到幻觉，降低置信度
            if hallucination_report.is_hallucination:
                answer.confidence *= 0.8
        
        # 达到最大迭代次数，返回当前结果
        return GroomingResult(
            query=query,
            answer=answer.content if answer.confidence >= self.min_confidence else "抱歉，我无法提供可靠的答案。",
            confidence=answer.confidence,
            citations=answer.citations,
            hallucination_report=hallucination_report,
            iterations=iteration
        )
    
    async def run_background_tasks(self) -> dict:
        """
        运行后台固化任务
        
        Returns:
            dict: 执行结果
        """
        if not self.consolidator or not self.pruner:
            return {"status": "skipped", "reason": "Memory manager not initialized"}
        
        results = {}
        
        # 运行知识固化
        consolidation_result = await self.consolidator.run_consolidation_cycle()
        results["consolidation"] = consolidation_result
        
        # 运行记忆修剪
        pruning_result = self.pruner.prune()
        results["pruning"] = pruning_result
        
        return results
