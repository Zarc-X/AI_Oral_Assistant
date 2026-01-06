"""
评价生成模块
根据评分结果生成中英文评价
"""
import logging
from typing import Dict
from .config import SCORE_CONFIG

logger = logging.getLogger(__name__)


class FeedbackGenerator:
    """评价生成器"""
    
    def __init__(self):
        """初始化评价生成器"""
        self.max_score = SCORE_CONFIG["max_score"]
    
    def generate_feedback(self, score_result: Dict) -> Dict[str, str]:
        """
        生成评价文本
        
        Args:
            score_result: 评分结果字典，包含分数和特征详情
            
        Returns:
            {"en": "英文评价", "zh": "中文评价"}
        """
        final_score = score_result["final_score"]
        delivery_score = score_result["delivery_score"]
        language_score = score_result["language_score"]
        
        # 生成英文评价
        feedback_en = self._generate_english_feedback(
            final_score, delivery_score, language_score, score_result
        )
        
        # 生成中文评价
        feedback_zh = self._generate_chinese_feedback(
            final_score, delivery_score, language_score, score_result
        )
        
        return {
            "en": feedback_en,
            "zh": feedback_zh
        }
    
    def _generate_english_feedback(self, final_score: float, delivery_score: float,
                                   language_score: float, score_result: Dict) -> str:
        """生成英文评价"""
        feedback_parts = []
        
        # 总体评价
        if final_score >= 3.5:
            feedback_parts.append("Excellent performance! Your speaking demonstrates strong fluency and clear expression.")
        elif final_score >= 3.0:
            feedback_parts.append("Good job! Your response shows solid speaking skills with room for improvement.")
        elif final_score >= 2.5:
            feedback_parts.append("Fair performance. You've made progress, but there are areas to work on.")
        elif final_score >= 2.0:
            feedback_parts.append("Your response needs improvement. Focus on both pronunciation and content.")
        else:
            feedback_parts.append("Keep practicing! Focus on the basics of pronunciation and grammar.")
        
        # 发音评价
        delivery_features = score_result.get("delivery_features", {})
        if delivery_score >= 3.0:
            feedback_parts.append("Your pronunciation is clear and your speaking pace is appropriate.")
        elif delivery_score >= 2.0:
            feedback_parts.append("Your pronunciation is understandable, but try to speak more fluently with fewer pauses.")
        else:
            feedback_parts.append("Work on your pronunciation and try to reduce long pauses and repetitions.")
        
        # 内容评价
        if language_score >= 3.0:
            feedback_parts.append("Your language use is effective with good vocabulary and grammar.")
        elif language_score >= 2.0:
            feedback_parts.append("Your language use is adequate, but try to use more varied vocabulary and complex sentences.")
        else:
            feedback_parts.append("Focus on using more diverse vocabulary and improving your grammar.")
        
        # 具体建议
        suggestions = self._get_specific_suggestions(score_result)
        if suggestions:
            feedback_parts.append("Suggestions: " + "; ".join(suggestions))
        
        return " ".join(feedback_parts)
    
    def _generate_chinese_feedback(self, final_score: float, delivery_score: float,
                                  language_score: float, score_result: Dict) -> str:
        """生成中文评价"""
        feedback_parts = []
        
        # 总体评价
        if final_score >= 3.5:
            feedback_parts.append("表现优秀！你的口语表达流利清晰。")
        elif final_score >= 3.0:
            feedback_parts.append("表现良好！你的口语技能扎实，仍有提升空间。")
        elif final_score >= 2.5:
            feedback_parts.append("表现一般。你已取得进步，但仍有需要改进的地方。")
        elif final_score >= 2.0:
            feedback_parts.append("需要改进。请同时关注发音和内容。")
        else:
            feedback_parts.append("继续练习！专注于发音和语法基础。")
        
        # 发音评价
        delivery_score_val = score_result.get("delivery_score", 0)
        if delivery_score_val >= 3.0:
            feedback_parts.append("你的发音清晰，语速适中。")
        elif delivery_score_val >= 2.0:
            feedback_parts.append("你的发音可以理解，但请尝试更流利地表达，减少停顿。")
        else:
            feedback_parts.append("请改进发音，减少长停顿和重复。")
        
        # 内容评价
        language_score_val = score_result.get("language_score", 0)
        if language_score_val >= 3.0:
            feedback_parts.append("你的语言使用有效，词汇和语法良好。")
        elif language_score_val >= 2.0:
            feedback_parts.append("你的语言使用尚可，但请尝试使用更多样化的词汇和复杂句式。")
        else:
            feedback_parts.append("请专注于使用更多样化的词汇并改进语法。")
        
        # 具体建议
        suggestions_zh = self._get_specific_suggestions_zh(score_result)
        if suggestions_zh:
            feedback_parts.append("建议：" + "；".join(suggestions_zh))
        
        return " ".join(feedback_parts)
    
    def _get_specific_suggestions(self, score_result: Dict) -> list:
        """获取具体建议（英文）"""
        suggestions = []
        delivery_features = score_result.get("delivery_features", {})
        language_features = score_result.get("language_features", {})
        
        # 发音相关建议
        if delivery_features.get("wpsecutt", 0) < 1.5:
            suggestions.append("Try to speak faster")
        if delivery_features.get("silpwd", 0) > 5:
            suggestions.append("Reduce pauses in your speech")
        if delivery_features.get("repfreq", 0) > 0.1:
            suggestions.append("Avoid repeating words")
        
        # 内容相关建议
        if language_features.get("types", 0) < 5:
            suggestions.append("Use more diverse word types")
        if language_features.get("cvamax", 0) < 0.7:
            suggestions.append("Try to provide more detailed answers")
        
        return suggestions
    
    def _get_specific_suggestions_zh(self, score_result: Dict) -> list:
        """获取具体建议（中文）"""
        suggestions = []
        delivery_features = score_result.get("delivery_features", {})
        language_features = score_result.get("language_features", {})
        
        # 发音相关建议
        if delivery_features.get("wpsecutt", 0) < 1.5:
            suggestions.append("尝试说得更快一些")
        if delivery_features.get("silpwd", 0) > 5:
            suggestions.append("减少说话中的停顿")
        if delivery_features.get("repfreq", 0) > 0.1:
            suggestions.append("避免重复单词")
        
        # 内容相关建议
        if language_features.get("types", 0) < 5:
            suggestions.append("使用更多样化的词类型")
        if language_features.get("cvamax", 0) < 0.7:
            suggestions.append("尝试提供更详细的回答")
        
        return suggestions

