"""
内容评分模块（Language Use Features）
实现6个语言使用相关指标的计算
"""
import numpy as np
import logging
from typing import Dict, List, Optional
from .config import LANGUAGE_WEIGHTS, TEXT_CONFIG

logger = logging.getLogger(__name__)

# 尝试导入spaCy，如果没有则使用简化方法
try:
    import spacy
    SPACY_AVAILABLE = True
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        logger.warning("spaCy英文模型未安装，使用简化方法")
        SPACY_AVAILABLE = False
        nlp = None
except ImportError:
    SPACY_AVAILABLE = False
    nlp = None
    logger.warning("spaCy未安装，使用简化方法")

# 尝试导入wordfreq
try:
    import wordfreq
    WORDFREQ_AVAILABLE = True
except ImportError:
    WORDFREQ_AVAILABLE = False
    logger.warning("wordfreq未安装，使用简化方法")


class LanguageScorer:
    """内容评分器"""
    
    def __init__(self):
        """初始化内容评分器"""
        self.weights = LANGUAGE_WEIGHTS
        self.nlp = nlp if SPACY_AVAILABLE else None
        
        # 词类型定义（简化版，如果spaCy不可用）
        self.word_types = {
            "noun": ["NN", "NNS", "NNP", "NNPS"],
            "verb": ["VB", "VBD", "VBG", "VBN", "VBP", "VBZ"],
            "adjective": ["JJ", "JJR", "JJS"],
            "adverb": ["RB", "RBR", "RBS"],
            "conjunction": ["CC"],
            "determiner": ["DT"],
            "preposition": ["IN"],
            "pronoun": ["PRP", "PRP$", "WP", "WP$"],
        }
    
    def calculate_all_features(self, text: str, audio_duration: float,
                              task_type: str = "independent") -> Dict[str, float]:
        """
        计算所有语言使用特征
        
        Args:
            text: 识别文本
            audio_duration: 音频时长（秒）
            task_type: 任务类型（"independent" 或 "integrated"）
            
        Returns:
            特征字典，包含6个指标的值
        """
        try:
            features = {}
            
            # 文本预处理
            words = text.split()
            word_count = len(words)
            
            if word_count == 0:
                return {key: 0.0 for key in self.weights.keys()}
            
            # 1. types - 词类型数量
            features["types"] = self._calculate_word_types(text)
            
            # 2. tpsec - 每秒词类型数
            features["tpsec"] = features["types"] / audio_duration if audio_duration > 0 else 0.0
            
            # 3. poscvamax - POS bigram对比（简化实现）
            features["poscvamax"] = self._calculate_pos_bigram_score(text)
            
            # 4. logfreq - 词汇频率
            features["logfreq"] = self._calculate_log_frequency(words)
            
            # 5. lmscore - 语言模型分数（语法正确性）
            features["lmscore"] = self._calculate_lm_score(text)
            
            # 6. cvamax - 单词数对比
            target_count = (TEXT_CONFIG["target_word_count_independent"] 
                          if task_type == "independent" 
                          else TEXT_CONFIG["target_word_count_integrated"])
            features["cvamax"] = self._calculate_word_count_score(word_count, target_count)
            
            return features
            
        except Exception as e:
            logger.error(f"计算语言特征失败: {e}")
            return {key: 0.0 for key in self.weights.keys()}
    
    def _calculate_word_types(self, text: str) -> float:
        """计算词类型数量"""
        if self.nlp:
            # 使用spaCy进行词性标注
            doc = self.nlp(text)
            pos_tags = set([token.pos_ for token in doc])
            return float(len(pos_tags))
        else:
            # 简化方法：使用NLTK或简单规则
            return self._calculate_word_types_simple(text)
    
    def _calculate_word_types_simple(self, text: str) -> float:
        """简化的词类型计算（基于常见词）"""
        words = text.lower().split()
        types_found = set()
        
        # 简单的词类型检测（基于常见词）
        common_nouns = ["person", "thing", "place", "time", "way", "day", "man", "woman"]
        common_verbs = ["is", "are", "was", "were", "have", "has", "do", "does", "go", "get"]
        common_adjectives = ["good", "bad", "big", "small", "important", "different"]
        common_adverbs = ["very", "really", "quite", "too", "also", "well"]
        common_conjunctions = ["and", "or", "but", "because", "if", "when"]
        common_determiners = ["the", "a", "an", "this", "that", "these", "those"]
        common_prepositions = ["in", "on", "at", "for", "with", "from", "to"]
        common_pronouns = ["i", "you", "he", "she", "it", "we", "they"]
        
        for word in words:
            word_clean = word.strip(".,!?;:")
            if word_clean in common_nouns:
                types_found.add("noun")
            elif word_clean in common_verbs:
                types_found.add("verb")
            elif word_clean in common_adjectives:
                types_found.add("adjective")
            elif word_clean in common_adverbs:
                types_found.add("adverb")
            elif word_clean in common_conjunctions:
                types_found.add("conjunction")
            elif word_clean in common_determiners:
                types_found.add("determiner")
            elif word_clean in common_prepositions:
                types_found.add("preposition")
            elif word_clean in common_pronouns:
                types_found.add("pronoun")
        
        # 至少应该有名词、动词、代词等基本类型
        return float(max(len(types_found), 3))  # 至少3种类型
    
    def _calculate_pos_bigram_score(self, text: str) -> float:
        """
        计算POS bigram分数
        简化实现：检测常见的语法模式
        """
        if self.nlp:
            doc = self.nlp(text)
            pos_tags = [token.pos_ for token in doc]
            
            if len(pos_tags) < 2:
                return 0.0
            
            # 计算bigram
            bigrams = [(pos_tags[i], pos_tags[i+1]) for i in range(len(pos_tags) - 1)]
            
            # 检测常见的正确语法模式
            good_patterns = [
                ("DET", "NOUN"),      # the cat
                ("ADJ", "NOUN"),      # big house
                ("NOUN", "VERB"),     # cat runs
                ("PRON", "VERB"),     # I think
                ("VERB", "DET"),      # see the
                ("VERB", "ADJ"),      # is good
            ]
            
            good_count = sum(1 for bg in bigrams if bg in good_patterns)
            return good_count / len(bigrams) if bigrams else 0.0
        else:
            # 简化方法：基于常见词序列
            return 0.5  # 默认中等分数
    
    def _calculate_log_frequency(self, words: List[str]) -> float:
        """计算平均log词频"""
        if WORDFREQ_AVAILABLE:
            try:
                frequencies = []
                for word in words:
                    word_clean = word.lower().strip(".,!?;:")
                    if word_clean:
                        freq = wordfreq.word_frequency(word_clean, 'en')
                        if freq > 0:
                            frequencies.append(np.log10(freq + 1e-10))
                
                return np.mean(frequencies) if frequencies else 0.0
            except Exception as e:
                logger.warning(f"词频计算失败: {e}")
                return 0.5
        else:
            # 简化方法：返回默认值
            return 0.5
    
    def _calculate_lm_score(self, text: str) -> float:
        """
        计算语言模型分数（语法正确性）
        简化实现：基于基本语法规则检查
        """
        if not text:
            return 0.0
        
        words = text.split()
        if len(words) < 3:
            return 0.3
        
        score = 0.5  # 基础分
        
        # 检查基本语法模式
        text_lower = text.lower()
        
        # 加分项：句子结构完整
        if "." in text or "!" in text or "?" in text:
            score += 0.2
        
        # 加分项：有连接词
        conjunctions = ["and", "or", "but", "because", "if", "when", "although"]
        if any(c in text_lower for c in conjunctions):
            score += 0.15
        
        # 加分项：有形容词和副词
        common_adjectives = ["good", "bad", "important", "different", "difficult", "easy"]
        common_adverbs = ["very", "really", "quite", "also", "well"]
        if any(adj in text_lower for adj in common_adjectives):
            score += 0.1
        if any(adv in text_lower for adv in common_adverbs):
            score += 0.05
        
        return min(score, 1.0)
    
    def _calculate_word_count_score(self, word_count: int, target_count: int) -> float:
        """
        计算单词数分数
        接近目标单词数得分越高
        """
        if target_count == 0:
            return 0.0
        
        # 计算与目标值的比例
        ratio = word_count / target_count
        
        # 理想范围：0.8 - 1.2
        if 0.8 <= ratio <= 1.2:
            return 1.0
        elif 0.6 <= ratio < 0.8 or 1.2 < ratio <= 1.5:
            return 0.7
        elif 0.4 <= ratio < 0.6 or 1.5 < ratio <= 2.0:
            return 0.4
        else:
            return 0.2
    
    def normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """归一化特征值到0-1范围"""
        normalized = {}
        
        max_values = {
            "types": 8.0,           # 最多8种词类型
            "tpsec": 2.0,            # 每秒词类型数
            "poscvamax": 1.0,        # 已经是0-1
            "logfreq": 1.0,          # log频率
            "lmscore": 1.0,          # 已经是0-1
            "cvamax": 1.0,           # 已经是0-1
        }
        
        for key, value in features.items():
            max_val = max_values.get(key, 1.0)
            if max_val > 0:
                normalized[key] = min(value / max_val, 1.0)
            else:
                normalized[key] = 0.0
        
        return normalized
    
    def calculate_language_score(self, features: Dict[str, float]) -> float:
        """
        计算内容总分（加权求和）
        
        Args:
            features: 归一化后的特征字典
            
        Returns:
            内容分数（0-1）
        """
        score = 0.0
        
        for feature_name, weight in self.weights.items():
            feature_value = features.get(feature_name, 0.0)
            score += feature_value * weight
        
        return score

