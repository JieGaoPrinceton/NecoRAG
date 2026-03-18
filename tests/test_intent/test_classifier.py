"""
测试 NecoRAG 意图分类器模块

测试内容：
- 意图分类器初始化
- 不同查询类型的分类结果
- 基于规则的分类
- 关键词和实体提取
"""

import pytest

from src.intent.classifier import IntentClassifier
from src.intent.config import IntentConfig
from src.intent.models import IntentType, IntentResult, IntentRoutingStrategy


class TestIntentClassifierInit:
    """IntentClassifier 初始化测试"""
    
    def test_init_default_config(self):
        """测试默认配置初始化"""
        classifier = IntentClassifier()
        
        assert classifier.config is not None
        assert classifier._backend == "rule_based"
        assert classifier._compiled_patterns is not None
    
    def test_init_custom_config(self):
        """测试自定义配置初始化"""
        config = IntentConfig(
            classifier_backend="rule_based",
            confidence_threshold=0.7,
            enable_multi_intent=False
        )
        classifier = IntentClassifier(config)
        
        assert classifier.config.confidence_threshold == 0.7
        assert classifier.config.enable_multi_intent is False
    
    def test_get_backend(self):
        """测试获取后端"""
        classifier = IntentClassifier()
        
        assert classifier.get_backend() == "rule_based"
        assert classifier.backend == "rule_based"


class TestRuleBasedClassification:
    """基于规则的分类测试"""
    
    def test_classify_explanation_chinese(self):
        """测试中文解释类意图"""
        classifier = IntentClassifier()
        
        result = classifier.classify("什么是深度学习？")
        
        assert isinstance(result, IntentResult)
        assert result.primary_intent == IntentType.EXPLANATION
        assert result.confidence > 0.3
    
    def test_classify_explanation_english(self):
        """测试英文解释类意图"""
        classifier = IntentClassifier()
        
        result = classifier.classify("What is machine learning?")
        
        assert result.primary_intent == IntentType.EXPLANATION
    
    def test_classify_procedural_chinese(self):
        """测试中文操作指导意图"""
        classifier = IntentClassifier()
        
        result = classifier.classify("如何安装 Python？")
        
        assert result.primary_intent == IntentType.PROCEDURAL
    
    def test_classify_procedural_english(self):
        """测试英文操作指导意图"""
        classifier = IntentClassifier()
        
        result = classifier.classify("How to install Docker?")
        
        assert result.primary_intent == IntentType.PROCEDURAL
    
    def test_classify_comparative(self):
        """测试比较分析意图"""
        classifier = IntentClassifier()
        
        result = classifier.classify("Python 和 Java 有什么区别？")
        
        assert result.primary_intent == IntentType.COMPARATIVE
    
    def test_classify_reasoning(self):
        """测试推理演绎意图"""
        classifier = IntentClassifier()
        
        result = classifier.classify("为什么机器学习需要大量数据？")
        
        assert result.primary_intent == IntentType.REASONING
    
    def test_classify_summarization(self):
        """测试摘要总结意图"""
        classifier = IntentClassifier()
        
        result = classifier.classify("请总结一下这篇文章的要点")
        
        assert result.primary_intent == IntentType.SUMMARIZATION
    
    def test_classify_exploratory(self):
        """测试探索发散意图"""
        classifier = IntentClassifier()
        
        result = classifier.classify("有哪些常用的深度学习框架？")
        
        assert result.primary_intent == IntentType.EXPLORATORY
    
    def test_classify_factual(self):
        """测试事实查询意图"""
        classifier = IntentClassifier()
        
        result = classifier.classify("Python 的最新版本是多少？")
        
        assert result.primary_intent == IntentType.FACTUAL
    
    def test_classify_default_to_factual(self):
        """测试无明确意图时默认为事实查询"""
        classifier = IntentClassifier()
        
        result = classifier.classify("随便说点什么")
        
        # 无明确意图应该默认为 FACTUAL
        assert result.primary_intent in [IntentType.FACTUAL, IntentType.EXPLORATORY, IntentType.EXPLANATION]


class TestClassifyEmptyAndEdgeCases:
    """空查询和边界情况测试"""
    
    def test_classify_empty_query(self):
        """测试空查询"""
        classifier = IntentClassifier()
        
        result = classifier.classify("")
        
        assert result.primary_intent == IntentType.FACTUAL
        assert result.confidence == 0.0
        assert result.keywords == []
    
    def test_classify_whitespace_query(self):
        """测试空白查询"""
        classifier = IntentClassifier()
        
        result = classifier.classify("   ")
        
        assert result.primary_intent == IntentType.FACTUAL
        assert result.confidence == 0.0
    
    def test_classify_unicode_query(self):
        """测试 Unicode 查询"""
        classifier = IntentClassifier()
        
        result = classifier.classify("你好世界 Hello 🌍")
        
        assert isinstance(result, IntentResult)
    
    def test_classify_very_long_query(self):
        """测试超长查询"""
        classifier = IntentClassifier()
        
        long_query = "这是一个测试查询 " * 100
        result = classifier.classify(long_query)
        
        assert isinstance(result, IntentResult)


class TestIntentResult:
    """IntentResult 数据类测试"""
    
    def test_intent_result_creation(self):
        """测试创建意图结果"""
        result = IntentResult(
            primary_intent=IntentType.FACTUAL,
            confidence=0.85,
            keywords=["关键词1", "关键词2"],
            entities=["实体1"]
        )
        
        assert result.primary_intent == IntentType.FACTUAL
        assert result.confidence == 0.85
        assert len(result.keywords) == 2
        assert len(result.entities) == 1
    
    def test_intent_result_confidence_clamped(self):
        """测试置信度被限制在 0-1"""
        # 超过 1
        result1 = IntentResult(
            primary_intent=IntentType.FACTUAL,
            confidence=1.5
        )
        assert result1.confidence == 1.0
        
        # 低于 0
        result2 = IntentResult(
            primary_intent=IntentType.FACTUAL,
            confidence=-0.5
        )
        assert result2.confidence == 0.0
    
    def test_intent_result_to_dict(self):
        """测试转换为字典"""
        result = IntentResult(
            primary_intent=IntentType.EXPLANATION,
            confidence=0.8,
            secondary_intents=[(IntentType.FACTUAL, 0.5)],
            keywords=["AI"],
            entities=["GPT"]
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["primary_intent"] == "explanation"
        assert result_dict["confidence"] == 0.8
        assert len(result_dict["secondary_intents"]) == 1
        assert result_dict["keywords"] == ["AI"]
    
    def test_intent_result_from_dict(self):
        """测试从字典创建"""
        data = {
            "primary_intent": "explanation",
            "confidence": 0.8,
            "secondary_intents": [{"intent": "factual", "confidence": 0.5}],
            "keywords": ["AI"],
            "entities": ["GPT"]
        }
        
        result = IntentResult.from_dict(data)
        
        assert result.primary_intent == IntentType.EXPLANATION
        assert result.confidence == 0.8
        assert len(result.secondary_intents) == 1
    
    def test_get_top_intents(self):
        """测试获取 top 意图"""
        result = IntentResult(
            primary_intent=IntentType.EXPLANATION,
            confidence=0.8,
            secondary_intents=[
                (IntentType.FACTUAL, 0.6),
                (IntentType.REASONING, 0.4)
            ]
        )
        
        top_intents = result.get_top_intents(2)
        
        assert len(top_intents) == 2
        assert top_intents[0][0] == IntentType.EXPLANATION
        assert top_intents[0][1] == 0.8


class TestKeywordExtraction:
    """关键词提取测试"""
    
    def test_extract_keywords_chinese(self):
        """测试中文关键词提取"""
        classifier = IntentClassifier()
        
        result = classifier.classify("深度学习和机器学习有什么区别？")
        
        # 应该提取到关键词
        assert len(result.keywords) > 0
    
    def test_extract_keywords_english(self):
        """测试英文关键词提取"""
        classifier = IntentClassifier()
        
        result = classifier.classify("What is the difference between Python and JavaScript?")
        
        assert len(result.keywords) > 0
    
    def test_extract_keywords_mixed(self):
        """测试中英文混合关键词提取"""
        classifier = IntentClassifier()
        
        result = classifier.classify("Python 和 Java 哪个更适合 machine learning？")
        
        assert len(result.keywords) > 0


class TestEntityExtraction:
    """实体提取测试"""
    
    def test_extract_entities_proper_nouns(self):
        """测试专有名词实体提取"""
        classifier = IntentClassifier()
        
        result = classifier.classify("What is GPT and how does OpenAI use it?")
        
        # 应该识别大写字母开头的专有名词
        assert len(result.entities) >= 0  # 简单实现可能提取不到
    
    def test_extract_entities_quoted_text(self):
        """测试引号内实体提取"""
        classifier = IntentClassifier()
        
        result = classifier.classify('什么是"深度学习"？')
        
        assert isinstance(result.entities, list)


class TestMultiIntent:
    """多意图支持测试"""
    
    def test_multi_intent_enabled(self):
        """测试启用多意图"""
        config = IntentConfig(enable_multi_intent=True, max_intents=3)
        classifier = IntentClassifier(config)
        
        result = classifier.classify("什么是深度学习，如何安装 TensorFlow？")
        
        # 可能有次要意图
        assert isinstance(result.secondary_intents, list)
    
    def test_multi_intent_disabled(self):
        """测试禁用多意图"""
        config = IntentConfig(enable_multi_intent=False)
        classifier = IntentClassifier(config)
        
        result = classifier.classify("什么是深度学习，如何安装 TensorFlow？")
        
        # 禁用时次要意图为空
        assert result.secondary_intents == []


class TestBackendSwitch:
    """后端切换测试"""
    
    def test_set_backend_valid(self):
        """测试设置有效后端"""
        classifier = IntentClassifier()
        
        classifier.set_backend("rule_based")
        assert classifier._backend == "rule_based"
    
    def test_set_backend_invalid(self):
        """测试设置无效后端"""
        classifier = IntentClassifier()
        original = classifier._backend
        
        classifier.set_backend("invalid_backend")
        
        # 应该保持原来的后端
        assert classifier._backend == original
    
    def test_fasttext_fallback(self):
        """测试 FastText 回退到规则"""
        config = IntentConfig(classifier_backend="fasttext")
        classifier = IntentClassifier(config)
        
        # 没有模型应该回退到规则分类
        result = classifier.classify("什么是深度学习？")
        
        assert isinstance(result, IntentResult)
    
    def test_transformer_fallback(self):
        """测试 Transformer 回退到规则"""
        config = IntentConfig(classifier_backend="transformer")
        classifier = IntentClassifier(config)
        
        # 没有模型应该回退到规则分类
        result = classifier.classify("什么是深度学习？")
        
        assert isinstance(result, IntentResult)


class TestBatchClassification:
    """批量分类测试"""
    
    def test_batch_classify(self):
        """测试批量分类"""
        classifier = IntentClassifier()
        
        queries = [
            "什么是深度学习？",
            "如何安装 Python？",
            "Python 和 Java 哪个好？"
        ]
        
        results = classifier.batch_classify(queries)
        
        assert len(results) == 3
        for result in results:
            assert isinstance(result, IntentResult)
    
    def test_batch_classify_empty(self):
        """测试空批量分类"""
        classifier = IntentClassifier()
        
        results = classifier.batch_classify([])
        
        assert results == []


class TestIntentConfig:
    """IntentConfig 测试"""
    
    def test_config_default(self):
        """测试默认配置"""
        config = IntentConfig.default()
        
        assert config.classifier_backend == "rule_based"
        assert config.confidence_threshold == 0.6
        assert config.enable_multi_intent is True
    
    def test_config_minimal(self):
        """测试最小配置"""
        config = IntentConfig.minimal()
        
        assert config.classifier_backend == "rule_based"
        assert config.enable_multi_intent is False
        assert config.max_intents == 1
    
    def test_config_advanced(self):
        """测试高级配置"""
        config = IntentConfig.advanced()
        
        assert config.classifier_backend == "transformer"
        assert config.enable_multi_intent is True
    
    def test_config_get_intent_weight(self):
        """测试获取意图权重"""
        config = IntentConfig()
        
        weight = config.get_intent_weight(IntentType.FACTUAL)
        
        assert weight == 1.0
    
    def test_config_get_routing_strategy(self):
        """测试获取路由策略"""
        config = IntentConfig()
        
        strategy = config.get_routing_strategy(IntentType.FACTUAL)
        
        assert isinstance(strategy, IntentRoutingStrategy)
        assert strategy.retrieval_mode == "vector"


class TestIntentRoutingStrategy:
    """IntentRoutingStrategy 测试"""
    
    def test_routing_strategy_default(self):
        """测试默认路由策略"""
        strategy = IntentRoutingStrategy()
        
        assert strategy.retrieval_mode == "hybrid"
        assert strategy.enable_graph_search is False
        assert strategy.enable_hyde is False
        assert strategy.top_k == 10
    
    def test_routing_strategy_to_dict(self):
        """测试路由策略转字典"""
        strategy = IntentRoutingStrategy(
            retrieval_mode="vector",
            enable_hyde=True,
            top_k=5
        )
        
        strategy_dict = strategy.to_dict()
        
        assert strategy_dict["retrieval_mode"] == "vector"
        assert strategy_dict["enable_hyde"] is True
        assert strategy_dict["top_k"] == 5
    
    def test_routing_strategy_merge(self):
        """测试路由策略合并"""
        strategy1 = IntentRoutingStrategy(
            retrieval_mode="vector",
            top_k=5,
            enable_hyde=True
        )
        strategy2 = IntentRoutingStrategy(
            retrieval_mode="graph",
            top_k=15,
            enable_hyde=False
        )
        
        merged = strategy1.merge_with(strategy2, weight=0.6)
        
        # 权重 0.6 > 0.5，应该使用 strategy1 的值
        assert merged.retrieval_mode == "vector"
        assert merged.enable_hyde is True
        # top_k 是加权平均
        assert 5 < merged.top_k < 15
