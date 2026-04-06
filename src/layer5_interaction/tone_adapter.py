"""
Tone Adapter - 语气适配器
"""

from typing import Dict


class ToneAdapter:
    """
    语气适配器
    
    支持多种语气风格：
    - formal: 专业严谨
    - friendly: 亲切友好
    - humorous: 幽默轻松
    """
    
    def __init__(self, auto_detect: bool = True):
        """
        初始化语气适配器
        
        Args:
            auto_detect: 是否自动检测语气
        """
        self.auto_detect = auto_detect
        
        # 语气模板
        self.templates = {
            "formal": {
                "prefix": "",
                "suffix": "",
                "connectors": ["因此", "综上所述", "根据分析"],
                "avoid_emojis": True
            },
            "friendly": {
                "prefix": "",
                "suffix": "~",
                "connectors": ["所以", "这样看来", "简单来说"],
                "avoid_emojis": False
            },
            "humorous": {
                "prefix": "哈哈，",
                "suffix": " 😸",
                "connectors": ["有趣的是", "惊喜吧", "猜猜看"],
                "avoid_emojis": False
            }
        }
    
    def adapt(self, content: str, style: str = "friendly") -> str:
        """
        适配语气
        
        Args:
            content: 原始内容
            style: 语气风格
            
        Returns:
            str: 适配后的内容
        """
        template = self.templates.get(style, self.templates["friendly"])
        
        # 添加前缀和后缀
        adapted = content
        
        if template["prefix"]:
            adapted = f"{template['prefix']}{adapted}"
        
        if template["suffix"]:
            adapted = f"{adapted}{template['suffix']}"
        
        # 移除或保留 emoji
        if template["avoid_emojis"]:
            adapted = self._remove_emojis(adapted)
        
        return adapted
    
    def inject_personality(
        self,
        content: str,
        style: str = "friendly"
    ) -> str:
        """
        注入个性化元素
        
        Args:
            content: 原始内容
            style: 语气风格
            
        Returns:
            str: 注入个性后的内容
        """
        template = self.templates.get(style, self.templates["friendly"])
        
        # 注入连接词
        lines = content.split('\n')
        if len(lines) > 1 and template["connectors"]:
            # 在段落间注入连接词
            connector = template["connectors"][0]
            adapted_lines = [lines[0]]
            
            for line in lines[1:]:
                if line.strip():
                    adapted_lines.append(f"{connector}，{line}")
                else:
                    adapted_lines.append(line)
            
            content = '\n'.join(adapted_lines)
        
        return content
    
    def _remove_emojis(self, text: str) -> str:
        """
        移除 emoji
        
        Args:
            text: 文本
            
        Returns:
            str: 移除 emoji 后的文本
        """
        # 简单实现：移除常见的 emoji
        emoji_ranges = [
            (0x1F600, 0x1F64F),  # 表情符号
            (0x1F300, 0x1F5FF),  # 符号和象形文字
            (0x1F680, 0x1F6FF),  # 交通和地图符号
            (0x2600, 0x26FF),    # 杂项符号
            (0x2700, 0x27BF),    # 装饰符号
        ]
        
        result = []
        for char in text:
            code = ord(char)
            is_emoji = any(start <= code <= end for start, end in emoji_ranges)
            if not is_emoji:
                result.append(char)
        
        return ''.join(result)
