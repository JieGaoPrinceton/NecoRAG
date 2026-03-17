"""
Detail Level Adapter - 详细程度适配器
"""

from typing import List


class DetailLevelAdapter:
    """
    详细程度适配器
    
    层级：
    - Level 1: 简洁摘要（1-2 句话）
    - Level 2: 标准回答（1 段话 + 要点）
    - Level 3: 详细解释（多段落 + 案例）
    - Level 4: 深度分析（完整报告）
    """
    
    def __init__(self, auto_adjust: bool = True):
        """
        初始化详细程度适配器
        
        Args:
            auto_adjust: 是否自动调整
        """
        self.auto_adjust = auto_adjust
    
    def adapt(
        self,
        content: str,
        level: int = 2
    ) -> str:
        """
        适配详细程度
        
        Args:
            content: 原始内容
            level: 详细程度级别 (1-4)
            
        Returns:
            str: 适配后的内容
        """
        if level <= 0:
            level = 1
        elif level > 4:
            level = 4
        
        if level == 1:
            return self.summarize(content)
        elif level == 2:
            return self.standardize(content)
        elif level == 3:
            return self.expand(content)
        else:  # level == 4
            return self.deep_analyze(content)
    
    def summarize(self, content: str) -> str:
        """
        生成简洁摘要
        
        Args:
            content: 原始内容
            
        Returns:
            str: 摘要
            
        TODO: 实现 LLM 摘要生成
        """
        # 最小实现：提取第一句
        sentences = content.split('。')
        if sentences:
            return sentences[0] + '。'
        return content[:100]
    
    def standardize(self, content: str) -> str:
        """
        生成标准回答
        
        Args:
            content: 原始内容
            
        Returns:
            str: 标准回答
        """
        # 添加要点标记
        lines = content.split('\n')
        
        if len(lines) > 3:
            # 提取要点
            summary = self.summarize(content)
            key_points = self._extract_key_points(lines)
            
            result = f"{summary}\n\n要点：\n"
            for i, point in enumerate(key_points[:3], 1):
                result += f"{i}. {point}\n"
            
            return result
        
        return content
    
    def expand(self, content: str) -> str:
        """
        扩展为详细解释
        
        Args:
            content: 原始内容
            
        Returns:
            str: 详细解释
            
        TODO: 实现内容扩展
        """
        # 最小实现：添加段落分隔
        paragraphs = content.split('\n\n')
        
        expanded = []
        for para in paragraphs:
            if para.strip():
                # 添加示例标记
                expanded.append(para)
                expanded.append("\n示例：\n[待补充示例]\n")
        
        return '\n'.join(expanded)
    
    def deep_analyze(self, content: str) -> str:
        """
        深度分析
        
        Args:
            content: 原始内容
            
        Returns:
            str: 深度分析报告
            
        TODO: 实现深度分析
        """
        # 最小实现：添加报告框架
        report = f"""
# 深度分析报告

## 摘要
{self.summarize(content)}

## 详细内容
{content}

## 关键要点
{self._format_key_points(content)}

## 延伸思考
[待补充]

## 参考资料
[待补充]
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
