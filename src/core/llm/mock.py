"""
Mock LLM 客户端实现

提供演示用的 LLM 客户端，不依赖任何外部服务。
用于开发、测试和演示场景。
"""

import random
import hashlib
import re
from typing import List, Optional, Dict, Any

from .base import BaseLLMClient


class MockLLMClient(BaseLLMClient):
    """
    Mock LLM 客户端
    
    提供确定性的响应（基于输入哈希），便于测试和演示。
    """
    
    def __init__(
        self,
        model_name: str = "mock-llm-v1",
        embedding_dim: int = 768,
        response_delay: float = 0.0,
        deterministic: bool = True
    ):
        """
        初始化 Mock LLM 客户端
        
        Args:
            model_name: 模型名称
            embedding_dim: 嵌入向量维度
            response_delay: 模拟响应延迟（秒）
            deterministic: 是否确定性响应（相同输入相同输出）
        """
        self._model_name = model_name
        self._embedding_dim = embedding_dim
        self._response_delay = response_delay
        self._deterministic = deterministic
        
        # 预定义的响应模板
        self._response_templates = {
            "question": [
                "根据您的问题，以下是我的分析和回答：\n\n{content}\n\n这个回答基于可用的知识库信息。",
                "针对「{query}」这个问题：\n\n{content}\n\n希望这个回答对您有帮助。",
            ],
            "hypothesis": [
                "假设性答案：{content}\n\n这是一个基于问题生成的假设性回答，用于增强检索。",
            ],
            "critique": [
                "评估结果：\n\n优点：答案逻辑清晰，基本覆盖了问题要点。\n缺点：部分细节可能需要更多证据支持。\n\n建议：{content}",
            ],
            "refine": [
                "修正后的答案：\n\n{content}\n\n修正要点：增强了证据支撑，优化了表述方式。",
            ],
            "default": [
                "这是一个演示响应。\n\n输入摘要：{summary}\n\n{content}",
            ]
        }
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def embedding_dimension(self) -> int:
        return self._embedding_dim
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        生成文本响应
        
        基于提示词内容智能选择响应模板。
        """
        import time
        if self._response_delay > 0:
            time.sleep(self._response_delay)
        
        # 检测响应类型
        response_type = self._detect_response_type(prompt)
        
        # 生成响应内容
        content = self._generate_content(prompt, response_type)
        
        # 选择模板
        templates = self._response_templates.get(
            response_type, 
            self._response_templates["default"]
        )
        
        if self._deterministic:
            # 确定性选择模板
            template_idx = self._hash_to_int(prompt) % len(templates)
        else:
            template_idx = random.randint(0, len(templates) - 1)
        
        template = templates[template_idx]
        
        # 填充模板
        query = self._extract_query(prompt)
        summary = prompt[:100] + "..." if len(prompt) > 100 else prompt
        
        return template.format(
            content=content,
            query=query,
            summary=summary
        )
    
    def embed(self, text: str) -> List[float]:
        """
        生成文本嵌入向量
        
        基于文本内容生成确定性的伪向量。
        """
        if self._deterministic:
            # 确定性向量：基于文本哈希
            return self._text_to_vector(text)
        else:
            # 随机向量
            return [random.gauss(0, 1) for _ in range(self._embedding_dim)]
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        return [self.embed(text) for text in texts]
    
    # ============== 私有方法 ==============
    
    def _detect_response_type(self, prompt: str) -> str:
        """检测响应类型"""
        prompt_lower = prompt.lower()
        
        if any(kw in prompt_lower for kw in ["假设", "hypothesis", "hyde"]):
            return "hypothesis"
        elif any(kw in prompt_lower for kw in ["评估", "批判", "critique", "评价"]):
            return "critique"
        elif any(kw in prompt_lower for kw in ["修正", "refine", "改进", "优化"]):
            return "refine"
        elif any(kw in prompt_lower for kw in ["?", "？", "问题", "什么", "如何", "为什么"]):
            return "question"
        else:
            return "default"
    
    def _generate_content(self, prompt: str, response_type: str) -> str:
        """生成响应内容"""
        # 提取关键信息
        keywords = self._extract_keywords(prompt)
        
        if response_type == "question":
            return self._generate_answer_content(prompt, keywords)
        elif response_type == "hypothesis":
            return self._generate_hypothesis_content(prompt, keywords)
        elif response_type == "critique":
            return self._generate_critique_content(keywords)
        elif response_type == "refine":
            return self._generate_refine_content(prompt, keywords)
        else:
            return f"处理您的请求涉及以下关键点：{', '.join(keywords[:5])}"
    
    def _generate_answer_content(self, prompt: str, keywords: List[str]) -> str:
        """生成问答内容"""
        if not keywords:
            return "根据可用信息，暂时无法提供详细答案。建议提供更多上下文信息。"
        
        points = [
            f"关于「{kw}」，这是一个重要的概念，在相关领域中具有特定意义。"
            for kw in keywords[:3]
        ]
        
        return "\n".join([
            "基于检索到的信息，以下是关键要点：",
            "",
            *[f"{i+1}. {p}" for i, p in enumerate(points)],
            "",
            "综上所述，这些概念相互关联，共同构成了问题的答案框架。"
        ])
    
    def _generate_hypothesis_content(self, prompt: str, keywords: List[str]) -> str:
        """生成假设答案内容"""
        if not keywords:
            return "这是一个需要更多上下文才能回答的问题。"
        
        return f"关于{keywords[0] if keywords else '这个问题'}，" \
               f"可能的答案涉及以下几个方面：" \
               f"首先是基本概念的理解，其次是具体应用场景，" \
               f"最后是相关的实践经验总结。"
    
    def _generate_critique_content(self, keywords: List[str]) -> str:
        """生成批判内容"""
        return "建议增加更多具体的数据支撑和引用来源，以提高答案的可信度。"
    
    def _generate_refine_content(self, prompt: str, keywords: List[str]) -> str:
        """生成修正内容"""
        return f"经过修正，答案更加准确地涵盖了{', '.join(keywords[:3])}等核心概念，" \
               f"并补充了必要的背景信息和具体示例。"
    
    def _extract_query(self, prompt: str) -> str:
        """提取查询内容"""
        # 尝试提取问题部分
        patterns = [
            r"问题[：:]\s*(.+?)(?:\n|$)",
            r"Query[：:]\s*(.+?)(?:\n|$)",
            r"请回答[：:]\s*(.+?)(?:\n|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # 返回前50个字符
        return prompt[:50].strip()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单实现）"""
        # 移除常见停用词
        stopwords = {
            "的", "了", "是", "在", "和", "与", "或", "这", "那", "有",
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "to", "of", "in", "for", "on", "with", "as", "at", "by"
        }
        
        # 简单分词
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
        
        # 过滤并去重
        keywords = []
        seen = set()
        for word in words:
            if len(word) >= 2 and word.lower() not in stopwords and word not in seen:
                keywords.append(word)
                seen.add(word)
        
        return keywords[:10]
    
    def _hash_to_int(self, text: str) -> int:
        """将文本哈希为整数"""
        return int(hashlib.md5(text.encode()).hexdigest(), 16)
    
    def _text_to_vector(self, text: str) -> List[float]:
        """
        将文本转换为确定性向量
        
        使用文本哈希作为随机种子，确保相同文本产生相同向量。
        """
        seed = self._hash_to_int(text)
        rng = random.Random(seed)
        
        # 生成单位向量（模长归一化）
        vector = [rng.gauss(0, 1) for _ in range(self._embedding_dim)]
        norm = sum(x*x for x in vector) ** 0.5
        
        if norm > 0:
            vector = [x / norm for x in vector]
        
        return vector


class MockLLMClientWithMemory(MockLLMClient):
    """
    带记忆功能的 Mock LLM 客户端
    
    可以记录所有调用，便于测试验证。
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._call_history: List[Dict[str, Any]] = []
    
    def generate(self, prompt: str, **kwargs) -> str:
        result = super().generate(prompt, **kwargs)
        self._call_history.append({
            "type": "generate",
            "prompt": prompt,
            "kwargs": kwargs,
            "result": result
        })
        return result
    
    def embed(self, text: str) -> List[float]:
        result = super().embed(text)
        self._call_history.append({
            "type": "embed",
            "text": text,
            "result_dim": len(result)
        })
        return result
    
    @property
    def call_history(self) -> List[Dict[str, Any]]:
        """返回调用历史"""
        return self._call_history.copy()
    
    def clear_history(self):
        """清除调用历史"""
        self._call_history.clear()
    
    def get_generate_calls(self) -> List[Dict[str, Any]]:
        """获取所有 generate 调用"""
        return [c for c in self._call_history if c["type"] == "generate"]
    
    def get_embed_calls(self) -> List[Dict[str, Any]]:
        """获取所有 embed 调用"""
        return [c for c in self._call_history if c["type"] == "embed"]
