"""
Purr Interface - 交互接口主类
"""

from typing import Optional, List
from necorag.memory.manager import MemoryManager
from necorag.grooming.models import GroomingResult
from necorag.purr.profile_manager import UserProfileManager
from necorag.purr.tone_adapter import ToneAdapter
from necorag.purr.detail_adapter import DetailLevelAdapter
from necorag.purr.visualizer import ThinkingChainVisualizer
from necorag.purr.models import UserProfile, Response
import uuid


class PurrInterface:
    """
    呼噜交互接口
    
    功能：
    - 情境自适应生成
    - 用户画像适配
    - 思维链可视化
    - 多模态输出
    """
    
    def __init__(
        self,
        memory: MemoryManager,
        llm_model: str = "default",
        default_tone: str = "friendly",
        default_detail_level: int = 2
    ):
        """
        初始化交互接口
        
        Args:
            memory: 记忆管理器
            llm_model: LLM 模型
            default_tone: 默认语气
            default_detail_level: 默认详细程度
        """
        self.memory = memory
        self.llm_model = llm_model
        
        # 初始化子组件
        self.profile_manager = UserProfileManager(memory.working_memory)
        self.tone_adapter = ToneAdapter()
        self.detail_adapter = DetailLevelAdapter()
        self.visualizer = ThinkingChainVisualizer()
        
        self.default_tone = default_tone
        self.default_detail_level = default_detail_level
    
    def respond(
        self,
        query: str,
        grooming_result: GroomingResult,
        session_id: Optional[str] = None,
        tone: Optional[str] = None,
        detail_level: Optional[int] = None
    ) -> Response:
        """
        生成响应
        
        Args:
            query: 查询文本
            grooming_result: 梳理结果
            session_id: 会话 ID
            tone: 语气风格
            detail_level: 详细程度
            
        Returns:
            Response: 响应对象
        """
        # 获取用户画像
        user_id = session_id or "anonymous"
        user_profile = self.profile_manager.get_profile(user_id)
        
        # 确定语气
        if tone is None:
            tone = user_profile.interaction_style
        
        # 确定详细程度
        if detail_level is None:
            detail_level = self._determine_detail_level(
                query,
                user_profile,
                grooming_result
            )
        
        # 适配内容
        content = grooming_result.answer
        
        # 语气适配
        content = self.tone_adapter.adapt(content, tone)
        content = self.tone_adapter.inject_personality(content, tone)
        
        # 详细程度适配
        content = self.detail_adapter.adapt(content, detail_level)
        
        # 生成思维链可视化
        thinking_chain = self._generate_thinking_chain(
            query,
            grooming_result
        )
        
        # 创建响应
        response = Response(
            content=content,
            thinking_chain=thinking_chain,
            tone=tone,
            detail_level=detail_level,
            citations=grooming_result.citations,
            metadata={
                "confidence": grooming_result.confidence,
                "iterations": grooming_result.iterations,
                "user_id": user_id
            }
        )
        
        # 更新用户画像
        from necorag.purr.models import Interaction
        interaction = Interaction(
            interaction_id=str(uuid.uuid4()),
            user_id=user_id,
            query=query,
            response=content
        )
        self.profile_manager.update_profile(user_id, interaction)
        
        return response
    
    def _determine_detail_level(
        self,
        query: str,
        user_profile: UserProfile,
        grooming_result: GroomingResult
    ) -> int:
        """
        确定详细程度
        
        Args:
            query: 查询文本
            user_profile: 用户画像
            grooming_result: 梳理结果
            
        Returns:
            int: 详细程度级别 (1-4)
        """
        # 基于用户专业水平
        level_map = {
            "beginner": 3,
            "intermediate": 2,
            "expert": 1
        }
        
        base_level = level_map.get(user_profile.professional_level, 2)
        
        # 基于查询复杂度调整
        if grooming_result.iterations > 2:
            # 复杂查询，提高详细程度
            base_level = min(base_level + 1, 4)
        
        return base_level
    
    def _generate_thinking_chain(
        self,
        query: str,
        grooming_result: GroomingResult
    ) -> str:
        """
        生成思维链可视化
        
        Args:
            query: 查询文本
            grooming_result: 梳理结果
            
        Returns:
            str: 可视化文本
        """
        # 构建检索路径
        retrieval_trace = [
            f"查询理解：{query}",
            "在语义记忆中检索相关内容",
            f"找到 {len(grooming_result.citations)} 条相关证据"
        ]
        
        # 构建证据来源
        evidence = [
            {"source": f"证据 {i+1}", "score": grooming_result.confidence}
            for i in range(len(grooming_result.citations))
        ]
        
        # 构建推理过程
        reasoning_chain = [
            f"置信度：{grooming_result.confidence:.2f}",
            f"迭代次数：{grooming_result.iterations}"
        ]
        
        if grooming_result.hallucination_report:
            reasoning_chain.append(
                f"幻觉检测：{'通过' if not grooming_result.hallucination_report.is_hallucination else '未通过'}"
            )
        
        # 生成可视化
        return self.visualizer.visualize(
            retrieval_trace=retrieval_trace,
            evidence=evidence,
            reasoning_chain=reasoning_chain
        )
    
    def get_user_preference(self, user_id: str) -> dict:
        """
        获取用户偏好
        
        Args:
            user_id: 用户 ID
            
        Returns:
            dict: 偏好分析结果
        """
        return self.profile_manager.analyze_preference(user_id)
