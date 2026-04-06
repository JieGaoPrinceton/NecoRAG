"""
NecoRAG 意图分类器模块

实现基于规则和机器学习的意图分类功能
"""

import re
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter
import logging

from .models import IntentType, IntentResult
from .config import IntentConfig
from src.core.base import BaseIntentClassifier


logger = logging.getLogger(__name__)


class IntentClassifier(BaseIntentClassifier):
    """
    意图分类器
    
    Intent classifier supporting rule-based, FastText, and Transformer backends.
    默认使用规则分类，无需额外依赖即可运行。
    
    使用示例:
    ```python
    from src.intent import IntentClassifier, IntentConfig
    
    config = IntentConfig.default()
    classifier = IntentClassifier(config)
    
    result = classifier.classify("什么是深度学习？")
    print(result.primary_intent)  # IntentType.EXPLANATION
    print(result.confidence)  # 0.85
    ```
    """
    
    def __init__(self, config: IntentConfig = None):
        """
        初始化意图分类器
        
        Args:
            config: 意图分类配置，None 则使用默认配置
        """
        self.config = config or IntentConfig.default()
        self._backend = self.config.classifier_backend
        
        # 编译关键词正则模式
        self._compiled_patterns: Dict[str, List[Tuple[re.Pattern, float]]] = {}
        self._compile_patterns()
        
        # 延迟加载的模型
        self._fasttext_model = None
        self._transformer_model = None
        self._tokenizer = None
        
        logger.info(f"IntentClassifier initialized with backend: {self._backend}")
    
    def _compile_patterns(self):
        """编译关键词正则模式"""
        for intent_type, pattern_config in self.config.keyword_patterns.items():
            patterns = []
            weight = pattern_config.get("weight", 1.0)
            
            # 编译中文模式
            for pattern in pattern_config.get("patterns_zh", []):
                try:
                    compiled = re.compile(pattern, re.IGNORECASE)
                    patterns.append((compiled, weight))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            
            # 编译英文模式
            for pattern in pattern_config.get("patterns_en", []):
                try:
                    compiled = re.compile(r'\b' + pattern + r'\b', re.IGNORECASE)
                    patterns.append((compiled, weight))
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
            
            self._compiled_patterns[intent_type] = patterns
    
    def classify(self, query: str) -> IntentResult:
        """
        对查询进行意图分类
        
        Args:
            query: 用户查询文本
            
        Returns:
            IntentResult: 意图分类结果
        """
        if not query or not query.strip():
            return IntentResult(
                primary_intent=IntentType.FACTUAL,
                confidence=0.0,
                keywords=[],
                entities=[]
            )
        
        # 根据后端选择分类方法
        if self._backend == "rule_based":
            return self._rule_based_classify(query)
        elif self._backend == "fasttext":
            return self._fasttext_classify(query)
        elif self._backend == "transformer":
            return self._transformer_classify(query)
        else:
            logger.warning(f"Unknown backend '{self._backend}', falling back to rule_based")
            return self._rule_based_classify(query)
    
    def _rule_based_classify(self, query: str) -> IntentResult:
        """
        基于规则的意图分类
        
        使用关键词模式匹配来识别意图，支持中英文。
        
        Args:
            query: 用户查询文本
            
        Returns:
            IntentResult: 意图分类结果
        """
        query_normalized = query.strip().lower()
        
        # 计算每个意图的得分
        intent_scores: Dict[str, float] = {}
        match_details: Dict[str, List[str]] = {}
        
        for intent_type, patterns in self._compiled_patterns.items():
            score = 0.0
            matched_patterns = []
            
            for pattern, weight in patterns:
                matches = pattern.findall(query_normalized)
                if matches:
                    # 根据匹配位置给予不同权重（开头匹配权重更高）
                    for match in matches:
                        match_text = match if isinstance(match, str) else match[0] if match else ""
                        position_factor = 1.0
                        if query_normalized.startswith(match_text):
                            position_factor = 1.3  # 开头匹配加权
                        score += weight * position_factor
                        matched_patterns.append(match_text)
            
            if score > 0:
                intent_scores[intent_type] = score
                match_details[intent_type] = matched_patterns
        
        # 提取关键词和实体
        keywords = self._extract_keywords(query)
        entities = self._extract_entities(query)
        
        # 如果没有匹配到任何意图，默认为 FACTUAL
        if not intent_scores:
            return IntentResult(
                primary_intent=IntentType.FACTUAL,
                confidence=0.5,  # 默认中等置信度
                secondary_intents=[],
                keywords=keywords,
                entities=entities
            )
        
        # 归一化得分并排序
        total_score = sum(intent_scores.values())
        normalized_scores = {
            k: v / total_score for k, v in intent_scores.items()
        }
        
        sorted_intents = sorted(
            normalized_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # 主要意图
        primary_intent_str, primary_confidence = sorted_intents[0]
        primary_intent = IntentType(primary_intent_str)
        
        # 置信度调整（基于得分差距）
        if len(sorted_intents) > 1:
            second_confidence = sorted_intents[1][1]
            confidence_gap = primary_confidence - second_confidence
            # 如果差距小，降低置信度
            if confidence_gap < 0.2:
                primary_confidence *= 0.8
        
        # 确保置信度在合理范围内
        primary_confidence = min(0.95, max(0.3, primary_confidence))
        
        # 次要意图
        secondary_intents = []
        if self.config.enable_multi_intent and len(sorted_intents) > 1:
            for intent_str, conf in sorted_intents[1:self.config.max_intents]:
                if conf >= self.config.confidence_threshold * 0.5:  # 次要意图阈值较低
                    secondary_intents.append((IntentType(intent_str), conf))
        
        return IntentResult(
            primary_intent=primary_intent,
            confidence=primary_confidence,
            secondary_intents=secondary_intents,
            keywords=keywords,
            entities=entities
        )
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        从查询中提取关键词
        
        Args:
            query: 查询文本
            
        Returns:
            关键词列表
        """
        keywords = []
        
        # 尝试使用 jieba 分词
        try:
            import jieba
            import jieba.analyse
            # 使用 TF-IDF 提取关键词
            keywords = jieba.analyse.extract_tags(query, topK=5)
        except ImportError:
            # jieba 不可用，使用简单的分词
            keywords = self._simple_extract_keywords(query)
        
        return keywords
    
    def _simple_extract_keywords(self, query: str) -> List[str]:
        """
        简单关键词提取（不依赖 jieba）
        
        Args:
            query: 查询文本
            
        Returns:
            关键词列表
        """
        # 停用词列表
        stopwords = {
            '的', '是', '在', '了', '和', '与', '或', '有', '被', '把',
            '这', '那', '什么', '怎么', '如何', '为什么', '哪', '吗', '呢',
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'to', 'of', 'and', 'or', 'in', 'on', 'at', 'for', 'with',
            'how', 'what', 'why', 'when', 'where', 'who', 'which'
        }
        
        # 提取词语（中文按字符，英文按空格）
        words = []
        
        # 英文单词
        english_words = re.findall(r'[a-zA-Z]+', query)
        words.extend([w.lower() for w in english_words if len(w) > 2])
        
        # 中文（简单地按长度分割）
        chinese_text = re.sub(r'[a-zA-Z0-9\s]', '', query)
        # 提取连续中文作为潜在关键词
        chinese_segments = re.findall(r'[\u4e00-\u9fff]{2,}', query)
        words.extend(chinese_segments)
        
        # 过滤停用词
        keywords = [w for w in words if w.lower() not in stopwords]
        
        # 统计词频，返回最常见的词
        counter = Counter(keywords)
        return [word for word, _ in counter.most_common(5)]
    
    def _extract_entities(self, query: str) -> List[str]:
        """
        从查询中提取实体
        
        Args:
            query: 查询文本
            
        Returns:
            实体列表
        """
        entities = []
        
        # 尝试使用 jieba 的词性标注
        try:
            import jieba.posseg as pseg
            words = pseg.cut(query)
            # 提取名词和专有名词
            for word, flag in words:
                if flag.startswith('n') or flag == 'eng':
                    if len(word) >= 2:
                        entities.append(word)
        except ImportError:
            # jieba 不可用，使用简单提取
            entities = self._simple_extract_entities(query)
        
        return entities[:10]  # 限制数量
    
    def _simple_extract_entities(self, query: str) -> List[str]:
        """
        简单实体提取（不依赖 jieba）
        
        Args:
            query: 查询文本
            
        Returns:
            实体列表
        """
        entities = []
        
        # 提取引号中的内容
        quoted = re.findall(r'[「」『』""\'\'](.*?)[「」『』""\'\'"]', query)
        entities.extend(quoted)
        
        # 提取大写字母开头的英文词（可能是专有名词）
        proper_nouns = re.findall(r'\b[A-Z][a-zA-Z]*\b', query)
        entities.extend(proper_nouns)
        
        # 提取可能的技术术语（包含大写字母或数字的词）
        tech_terms = re.findall(r'\b[a-zA-Z]*[A-Z0-9][a-zA-Z0-9]*\b', query)
        entities.extend([t for t in tech_terms if len(t) >= 2])
        
        # 去重
        return list(dict.fromkeys(entities))
    
    def _fasttext_classify(self, query: str) -> IntentResult:
        """
        基于 FastText 的意图分类
        
        Args:
            query: 查询文本
            
        Returns:
            IntentResult: 意图分类结果
        """
        # 加载 FastText 模型
        if self._fasttext_model is None:
            try:
                import fasttext
                if self.config.fasttext_model_path:
                    self._fasttext_model = fasttext.load_model(self.config.fasttext_model_path)
                else:
                    logger.warning("FastText model path not configured, falling back to rule_based")
                    return self._rule_based_classify(query)
            except ImportError:
                logger.warning("fasttext not installed, falling back to rule_based")
                return self._rule_based_classify(query)
            except Exception as e:
                logger.error(f"Failed to load FastText model: {e}")
                return self._rule_based_classify(query)
        
        # 预处理查询
        query_processed = query.replace('\n', ' ').strip()
        
        # 预测
        labels, scores = self._fasttext_model.predict(query_processed, k=self.config.max_intents)
        
        # 解析结果
        keywords = self._extract_keywords(query)
        entities = self._extract_entities(query)
        
        # 转换标签格式 (__label__xxx -> xxx)
        intents = []
        for label, score in zip(labels, scores):
            intent_str = label.replace('__label__', '')
            try:
                intent_type = IntentType(intent_str)
                intents.append((intent_type, float(score)))
            except ValueError:
                continue
        
        if not intents:
            return self._rule_based_classify(query)
        
        primary_intent, primary_confidence = intents[0]
        secondary_intents = intents[1:] if len(intents) > 1 else []
        
        return IntentResult(
            primary_intent=primary_intent,
            confidence=primary_confidence,
            secondary_intents=secondary_intents,
            keywords=keywords,
            entities=entities
        )
    
    def _transformer_classify(self, query: str) -> IntentResult:
        """
        基于 Transformer 的意图分类
        
        Args:
            query: 查询文本
            
        Returns:
            IntentResult: 意图分类结果
        """
        # 加载 Transformer 模型
        if self._transformer_model is None:
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer
                import torch
                
                self._tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
                self._transformer_model = AutoModelForSequenceClassification.from_pretrained(
                    self.config.model_name,
                    num_labels=len(IntentType)
                )
                self._transformer_model.eval()
            except ImportError:
                logger.warning("transformers not installed, falling back to rule_based")
                return self._rule_based_classify(query)
            except Exception as e:
                logger.error(f"Failed to load Transformer model: {e}")
                return self._rule_based_classify(query)
        
        try:
            import torch
            
            # 编码
            inputs = self._tokenizer(
                query,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            
            # 推理
            with torch.no_grad():
                outputs = self._transformer_model(**inputs)
                logits = outputs.logits
                probs = torch.softmax(logits, dim=-1)[0]
            
            # 获取 top-k 预测
            top_k = min(self.config.max_intents, len(IntentType))
            top_probs, top_indices = torch.topk(probs, top_k)
            
            # 转换为意图
            intent_types = list(IntentType)
            intents = [
                (intent_types[idx.item()], prob.item())
                for idx, prob in zip(top_indices, top_probs)
            ]
            
            keywords = self._extract_keywords(query)
            entities = self._extract_entities(query)
            
            primary_intent, primary_confidence = intents[0]
            secondary_intents = intents[1:] if len(intents) > 1 else []
            
            return IntentResult(
                primary_intent=primary_intent,
                confidence=primary_confidence,
                secondary_intents=secondary_intents,
                keywords=keywords,
                entities=entities
            )
            
        except Exception as e:
            logger.error(f"Transformer classification failed: {e}")
            return self._rule_based_classify(query)
    
    def batch_classify(self, queries: List[str]) -> List[IntentResult]:
        """
        批量分类
        
        Args:
            queries: 查询列表
            
        Returns:
            IntentResult 列表
        """
        return [self.classify(query) for query in queries]
    
    def get_backend(self) -> str:
        """获取当前使用的分类后端"""
        return self._backend
    
    @property
    def backend(self) -> str:
        """返回分类器后端名称 (实现 BaseIntentClassifier 抽象属性)"""
        return self._backend
    
    def set_backend(self, backend: str):
        """
        设置分类后端
        
        Args:
            backend: 后端名称 (rule_based, fasttext, transformer)
        """
        if backend in ["rule_based", "fasttext", "transformer"]:
            self._backend = backend
            logger.info(f"Backend changed to: {backend}")
        else:
            logger.warning(f"Invalid backend '{backend}', keeping current: {self._backend}")
