"""
Grooming Agent - 梳理校正代理
巩固层核心组件，知识的异步固化、幻觉自检与记忆修剪
"""

from src.grooming.agent import GroomingAgent
from src.grooming.generator import Generator
from src.grooming.critic import Critic
from src.grooming.refiner import Refiner
from src.grooming.hallucination import HallucinationDetector
from src.grooming.consolidator import KnowledgeConsolidator
from src.grooming.pruner import MemoryPruner
from src.grooming.models import GroomingResult, HallucinationReport

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
