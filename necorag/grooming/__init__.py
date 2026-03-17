"""
Grooming Agent - 梳理校正代理
巩固层核心组件，知识的异步固化、幻觉自检与记忆修剪
"""

from necorag.grooming.agent import GroomingAgent
from necorag.grooming.generator import Generator
from necorag.grooming.critic import Critic
from necorag.grooming.refiner import Refiner
from necorag.grooming.hallucination import HallucinationDetector
from necorag.grooming.consolidator import KnowledgeConsolidator
from necorag.grooming.pruner import MemoryPruner
from necorag.grooming.models import GroomingResult, HallucinationReport

__all__ = [
    "GroomingAgent",
    "Generator",
    "Critic",
    "Refiner",
    "HallucinationDetector",
    "KnowledgeConsolidator",
    "MemoryPruner",
    "GroomingResult",
    "HallucinationReport",
]
