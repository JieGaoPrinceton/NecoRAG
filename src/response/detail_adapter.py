"""Detail Level Adapter - 详细程度适配器

提供基于详细级别的内容适配功能，支持：
- Level 1: 简洁摘要
- Level 2: 标准回答
- Level 3: 详细解释
- Level 4: 深度分析

支持 LLM 增强模式，也可退化为简单规则处理。
"""

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.base import BaseLLMClient


class DetailLevelAdapter:
    """
    详细程度适配器
    
    层级：
    - Level 1: 简洁摘要（1-2 句话）
    - Level 2: 标准回答（1 段话 + 要点）
    - Level 3: 详细解释（多段落 + 案例）
    - Level 4: 深度分析（完整报告）
    
    支持 LLM 增强模式，无 LLM 时退化为简单文本处理。
    """
    
    # 内容长度阈值
    SHORT_CONTENT_THRESHOLD = 100  # 需要扩展的内容长度阈值
    LONG_CONTENT_THRESHOLD = 500   # 需要摘要的内容长度阈值
    
    def __init__(
        self,
        auto_adjust: bool = True,
        llm_client: Optional["BaseLLMClient"] = None
    ):
        """
        初始化详细程度适配器
        
        Args:
            auto_adjust: 是否自动调整
            llm_client: LLM 客户端（可选，为 None 时使用退化模式）
        """
        self.auto_adjust = auto_adjust
        self._llm_client = llm_client
    
    @property
    def llm_enabled(self) -> bool:
        """检查 LLM 是否可用"""
        return self._llm_client is not None
    
    def set_llm_client(self, llm_client: Optional["BaseLLMClient"]) -> None:
        """
        设置 LLM 客户端
        
        Args:
            llm_client: LLM 客户端实例
        """
        self._llm_client = llm_client
    
    def adapt(
        self,
        content: str,
        level: int = 2,
        query: Optional[str] = None
    ) -> str:
        """
        适配详细程度
        
        Args:
            content: 原始内容
            level: 详细程度级别 (1-4)
            query: 原始查询（可选，用于生成更相关的内容）
            
        Returns:
            str: 适配后的内容
        """
        if level <= 0:
            level = 1
        elif level > 4:
            level = 4
        
        if level == 1:
            return self.summarize(content, query)
        elif level == 2:
            return self.standardize(content, query)
        elif level == 3:
            return self.expand(content, query)
        else:  # level == 4
            return self.deep_analyze(content, query)
    
    def summarize(self, content: str, query: Optional[str] = None) -> str:
        """
        生成简洁摘要
        
        Args:
            content: 原始内容
            query: 原始查询（可选，用于生成更相关的摘要）
            
        Returns:
            str: 摘要
        """
        # 短内容直接返回
        if len(content) <= self.SHORT_CONTENT_THRESHOLD:
            return content
        
        # 如果有 LLM，使用 LLM 生成摘要
        if self._llm_client is not None:
            return self._llm_summarize(content, query)
        
        # 退化模式：提取第一句或截断
        return self._fallback_summarize(content)
    
    def _llm_summarize(self, content: str, query: Optional[str] = None) -> str:
        """
        使用 LLM 生成摘要
        
        Args:
            content: 原始内容
            query: 原始查询
            
        Returns:
            str: LLM 生成的摘要
        """
        context_hint = f"\n针对问题「{query}」，" if query else "\n"
        
        prompt = f"""请将以下内容总结为简洁的摘要（1-2句话）：

{content}
{context_hint}请生成简洁、准确的摘要："""
        
        try:
            summary = self._llm_client.generate(
                prompt=prompt,
                max_tokens=200,
                temperature=0.3
            )
            return summary.strip()
        except Exception:
            # LLM 调用失败时退化
            return self._fallback_summarize(content)
    
    def _fallback_summarize(self, content: str) -> str:
        """
        退化模式摘要（无 LLM 时使用）
        
        Args:
            content: 原始内容
            
        Returns:
            str: 简单处理后的摘要
        """
        # 提取第一句
        sentences = content.split('。')
        if sentences and sentences[0].strip():
            first_sentence = sentences[0].strip()
            if len(first_sentence) > 20:  # 第一句足够长
                return first_sentence + '。'
        
        # 否则截断前100字符
        truncated = content[:100].strip()
        if len(content) > 100:
            truncated += '...'
        return truncated
    
    def standardize(self, content: str, query: Optional[str] = None) -> str:
        """
        生成标准回答
        
        Args:
            content: 原始内容
            query: 原始查询（可选）
            
        Returns:
            str: 标准回答
        """
        # 添加要点标记
        lines = content.split('\n')
        
        if len(lines) > 3:
            # 提取要点
            summary = self.summarize(content, query)
            key_points = self._extract_key_points(lines)
            
            result = f"{summary}\n\n要点：\n"
            for i, point in enumerate(key_points[:3], 1):
                result += f"{i}. {point}\n"
            
            return result
        
        return content
    
    def expand(self, content: str, query: Optional[str] = None) -> str:
        """
        扩展为详细解释
        
        Args:
            content: 原始内容
            query: 原始查询（可选，用于生成更相关的扩展）
            
        Returns:
            str: 详细解释
        """
        # 已经足够详细的内容不需要扩展
        if len(content) >= self.LONG_CONTENT_THRESHOLD:
            return content
        
        # 如果有 LLM，使用 LLM 扩展内容
        if self._llm_client is not None:
            return self._llm_expand(content, query)
        
        # 退化模式：添加结构化框架
        return self._fallback_expand(content)
    
    def _llm_expand(self, content: str, query: Optional[str] = None) -> str:
        """
        使用 LLM 扩展内容
        
        Args:
            content: 原始内容
            query: 原始查询
            
        Returns:
            str: LLM 扩展后的内容
        """
        context_hint = f"原始问题是「{query}」。\n\n" if query else ""
        
        prompt = f"""请将以下简短的回答扩展为更详细的解释，添加必要的背景信息、示例和说明：

{context_hint}原始回答：
{content}

请生成详细的扩展内容（包含背景说明、具体示例、注意事项等）："""
        
        try:
            expanded = self._llm_client.generate(
                prompt=prompt,
                max_tokens=1024,
                temperature=0.5
            )
            return expanded.strip()
        except Exception:
            # LLM 调用失败时退化
            return self._fallback_expand(content)
    
    def _fallback_expand(self, content: str) -> str:
        """
        退化模式扩展（无 LLM 时使用）
        
        Args:
            content: 原始内容
            
        Returns:
            str: 添加结构框架后的内容
        """
        paragraphs = content.split('\n\n')
        
        expanded = []
        for i, para in enumerate(paragraphs):
            if para.strip():
                expanded.append(para)
                if i == 0:  # 第一段后添加示例提示
                    expanded.append("\n**示例说明**：[此处可补充具体示例]\n")
        
        # 添加补充说明
        expanded.append("\n**补充说明**")
        expanded.append("以上内容涵盖了主要要点，更多细节可根据具体场景补充。")
        
        return '\n'.join(expanded)
    
    def deep_analyze(self, content: str, query: Optional[str] = None) -> str:
        """
        深度分析
        
        对内容进行多角度深度分析，生成完整报告。
        
        Args:
            content: 原始内容
            query: 原始查询（可选）
            
        Returns:
            str: 深度分析报告
        """
        # 如果有 LLM，使用 LLM 进行深度分析
        if self._llm_client is not None:
            return self._llm_deep_analyze(content, query)
        
        # 退化模式：构建结构化报告框架
        return self._fallback_deep_analyze(content)
    
    def _llm_deep_analyze(self, content: str, query: Optional[str] = None) -> str:
        """
        使用 LLM 进行深度分析
        
        Args:
            content: 原始内容
            query: 原始查询
            
        Returns:
            str: LLM 生成的深度分析报告
        """
        context_hint = f"用户的问题是「{query}」。\n\n" if query else ""
        
        prompt = f"""请对以下内容进行多角度深度分析，生成完整的分析报告：

{context_hint}待分析内容：
{content}

请从以下角度进行分析：
1. **核心观点总结**：提炼关键信息
2. **背景与上下文**：补充必要的背景知识
3. **多角度分析**：从不同角度（如技术、实践、理论等）进行分析
4. **潜在问题与风险**：指出可能的问题或需要注意的地方
5. **延伸思考与建议**：提供进一步的思考方向

请生成结构化的深度分析报告："""
        
        try:
            analysis = self._llm_client.generate(
                prompt=prompt,
                max_tokens=2048,
                temperature=0.6
            )
            return analysis.strip()
        except Exception:
            # LLM 调用失败时退化
            return self._fallback_deep_analyze(content)
    
    def _fallback_deep_analyze(self, content: str) -> str:
        """
        退化模式深度分析（无 LLM 时使用）
        
        Args:
            content: 原始内容
            
        Returns:
            str: 结构化报告框架
        """
        summary = self._fallback_summarize(content)
        key_points = self._format_key_points(content)
        
        report = f"""# 深度分析报告

## 摘要
{summary}

## 详细内容
{content}

## 关键要点
{key_points if key_points.strip() else "- 请参阅上述详细内容"}

## 多角度分析

### 技术角度
[需要 LLM 支持以生成详细分析]

### 实践角度
[需要 LLM 支持以生成详细分析]

## 延伸思考
- 可考虑相关领域的关联知识
- 建议结合实际场景进行验证

## 参考资料
[可根据需要补充相关文档或链接]
"""
        return report.strip()
    
    def _extract_key_points(self, lines: List[str]) -> List[str]:
        """
        提取关键要点
        
        Args:
            lines: 文本行列表
            
        Returns:
            List[str]: 要点列表
        """
        key_points = []
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行和短行
            if len(line) < 20:
                continue
            
            # 提取包含关键词的句子
            keywords = ['重要', '关键', '核心', '主要', '首先', '其次']
            if any(kw in line for kw in keywords):
                key_points.append(line)
        
        return key_points
    
    def _format_key_points(self, content: str) -> str:
        """
        格式化关键要点
        
        Args:
            content: 内容
            
        Returns:
            str: 格式化的要点
        """
        lines = content.split('\n')
        key_points = self._extract_key_points(lines)
        
        formatted = ""
        for i, point in enumerate(key_points[:5], 1):
            formatted += f"{i}. {point}\n"
        
        return formatted
