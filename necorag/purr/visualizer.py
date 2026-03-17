"""
Thinking Chain Visualizer - 思维链可视化器
"""

from typing import List, Dict, Any
from necorag.purr.models import RetrievalVisualization


class ThinkingChainVisualizer:
    """
    思维链可视化器
    
    展示：
    1. 检索路径：查询 → 实体识别 → 向量检索 → 图谱推理 → 结果融合
    2. 证据来源：每个断言的证据 ID 和相关度
    3. 推理过程：多跳推理的逻辑链条
    """
    
    def __init__(
        self,
        show_trace: bool = True,
        show_evidence: bool = True,
        show_reasoning: bool = True
    ):
        """
        初始化可视化器
        
        Args:
            show_trace: 是否显示检索路径
            show_evidence: 是否显示证据来源
            show_reasoning: 是否显示推理过程
        """
        self.show_trace = show_trace
        self.show_evidence = show_evidence
        self.show_reasoning = show_reasoning
    
    def visualize(
        self,
        retrieval_trace: List[str] = None,
        evidence: List[Dict[str, Any]] = None,
        reasoning_chain: List[str] = None
    ) -> str:
        """
        生成可视化输出
        
        Args:
            retrieval_trace: 检索路径
            evidence: 证据列表
            reasoning_chain: 推理链条
            
        Returns:
            str: 可视化文本
        """
        visualization_parts = []
        
        # 检索路径
        if self.show_trace and retrieval_trace:
            trace_section = self._visualize_trace(retrieval_trace)
            visualization_parts.append(trace_section)
        
        # 证据来源
        if self.show_evidence and evidence:
            evidence_section = self._visualize_evidence(evidence)
            visualization_parts.append(evidence_section)
        
        # 推理过程
        if self.show_reasoning and reasoning_chain:
            reasoning_section = self._visualize_reasoning(reasoning_chain)
            visualization_parts.append(reasoning_section)
        
        return '\n\n'.join(visualization_parts)
    
    def _visualize_trace(self, trace: List[str]) -> str:
        """
        可视化检索路径
        
        Args:
            trace: 检索步骤列表
            
        Returns:
            str: 可视化文本
        """
        lines = ["🔍 检索路径："]
        
        for i, step in enumerate(trace, 1):
            lines.append(f"  {i}. {step}")
        
        return '\n'.join(lines)
    
    def _visualize_evidence(self, evidence: List[Dict[str, Any]]) -> str:
        """
        可视化证据来源
        
        Args:
            evidence: 证据列表
            
        Returns:
            str: 可视化文本
        """
        lines = ["📚 证据来源："]
        
        for i, ev in enumerate(evidence[:5], 1):  # 最多显示 5 条
            source = ev.get("source", "未知来源")
            score = ev.get("score", 0)
            
            lines.append(f"  - [证据 {i}] {source} (相关度: {score:.2f})")
        
        return '\n'.join(lines)
    
    def _visualize_reasoning(self, chain: List[str]) -> str:
        """
        可视化推理过程
        
        Args:
            chain: 推理链条
            
        Returns:
            str: 可视化文本
        """
        lines = ["🧠 推理过程："]
        
        for i, step in enumerate(chain, 1):
            lines.append(f"  {step}")
        
        return '\n'.join(lines)
    
    def visualize_as_dict(
        self,
        retrieval_trace: List[str] = None,
        evidence: List[Dict[str, Any]] = None,
        reasoning_chain: List[str] = None
    ) -> RetrievalVisualization:
        """
        生成结构化可视化对象
        
        Args:
            retrieval_trace: 检索路径
            evidence: 证据列表
            reasoning_chain: 推理链条
            
        Returns:
            RetrievalVisualization: 可视化对象
        """
        return RetrievalVisualization(
            query_understanding=retrieval_trace[0] if retrieval_trace else "",
            retrieval_steps=retrieval_trace or [],
            evidence_sources=evidence or [],
            reasoning_chain=reasoning_chain or []
        )
