"""
Refinement Agent - 精炼代理
巩固层核心组件，知识的异步固化、幻觉自检与记忆修剪
"""

from src.refinement.agent import RefinementAgent
from src.refinement.generator import Generator
from src.refinement.critic import Critic
from src.refinement.refiner import Refiner
from src.refinement.hallucination import HallucinationDetector
from src.refinement.consolidator import KnowledgeConsolidator
from src.refinement.pruner import MemoryPruner
from src.refinement.models import RefinementResult, HallucinationReport

__all__ = [
    "RefinementAgent",
    "Generator",
    "Critic",
    "Refiner",
    "HallucinationDetector",
    "KnowledgeConsolidator",
    "MemoryPruner",
    "RefinementResult",
    "HallucinationReport",
]
