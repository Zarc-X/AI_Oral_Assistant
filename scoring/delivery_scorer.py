"""
发音评分模块（Delivery Features）
实现12个发音相关指标的计算
"""
import numpy as np
import logging
from typing import Dict, Optional
from audio_analyzer import AudioAnalyzer
from config import DELIVERY_WEIGHTS, TEXT_CONFIG

logger = logging.getLogger(__name__)


class DeliveryScorer:
    """发音评分器"""
    
    def __init__(self):
        """初始化发音评分器"""
        self.audio_analyzer = AudioAnalyzer()
        self.weights = DELIVERY_WEIGHTS
    
    def calculate_all_features(self, audio_path: str, text: str, 
                              asr_confidence: Optional[float] = None) -> Dict[str, float]:
        """
        计算所有发音特征
        
        Args:
            audio_path: 音频文件路径
            text: 识别文本
            asr_confidence: ASR平均置信度（可选）
            
        Returns:
            特征字典，包含12个指标的值
        """
        try:
            # 加载音频
            audio = self.audio_analyzer.load_audio(audio_path)
            duration = self.audio_analyzer.get_audio_duration(audio)
            
            # 文本预处理
            words = text.lower().split()
            
            # 计算各个特征
            features = {}
            
            # 1. wpsecutt - 语速（每秒单词数）
            features["wpsecutt"] = self._calculate_speaking_rate(words, duration)
            
            # 2. wdpchk - 平均语音块长度
            # 3. wdpchkmeandev - 语音块长度偏差
            chunk_lengths, chunk_deviation = self.audio_analyzer.calculate_speech_chunks(audio, words)
            features["wdpchk"] = np.mean(chunk_lengths) if chunk_lengths else 0.0
            features["wdpchkmeandev"] = chunk_deviation
            
            # 4. silpwd - 短静音频率（>0.15s）
            # 5. longpfreq - 长静音频率（>0.5s）
            short_pauses, long_pauses = self.audio_analyzer.detect_silences(audio)
            features["silpwd"] = len(short_pauses)
            features["longpfreq"] = len(long_pauses)
            
            # 6. repfreq - 重复频率
            features["repfreq"] = self._calculate_repetition_frequency(words)
            
            # 7. ipc - 中断点频率（自我修正）
            features["ipc"] = self._calculate_interruption_points(text)
            
            # 8. dpsec - 不流畅词频率
            features["dpsec"] = self._calculate_disfluency_frequency(words, duration)
            
            # 9. stretimemean - 重音音节平均距离
            # 10. stresyllmdev - 重音音节距离偏差
            stress_times = self.audio_analyzer.detect_stressed_syllables(audio)
            stress_mean, stress_dev = self.audio_analyzer.calculate_stress_intervals(stress_times)
            features["stretimemean"] = stress_mean
            features["stresyllmdev"] = stress_dev
            
            # 11. conftimeavg - ASR置信度
            features["conftimeavg"] = asr_confidence if asr_confidence is not None else 0.5
            
            # 12. L6 - 发音质量评分（简化：基于ASR置信度和重音检测）
            features["L6"] = self._calculate_pronunciation_quality(
                asr_confidence, stress_times, duration
            )
            
            return features
            
        except Exception as e:
            logger.error(f"计算发音特征失败: {e}")
            # 返回默认值
            return {key: 0.0 for key in self.weights.keys()}
    
    def _calculate_speaking_rate(self, words: list, duration: float) -> float:
        """计算语速（每秒单词数）"""
        if duration <= 0:
            return 0.0
        return len(words) / duration
    
    def _calculate_repetition_frequency(self, words: list) -> float:
        """计算重复频率"""
        if len(words) < 2:
            return 0.0
        
        repetitions = 0
        for i in range(len(words) - 1):
            if words[i] == words[i + 1]:
                repetitions += 1
        
        return repetitions / len(words) if words else 0.0
    
    def _calculate_interruption_points(self, text: str) -> float:
        """
        计算中断点频率（自我修正）
        检测模式：单词重复、修正（如 "I go... went"）
        """
        words = text.lower().split()
        if len(words) < 3:
            return 0.0
        
        interruption_points = 0
        
        # 检测重复后修正的模式
        for i in range(len(words) - 2):
            # 简单模式：重复词后跟不同词（可能是修正）
            if words[i] == words[i + 1] and words[i + 1] != words[i + 2]:
                interruption_points += 1
        
        # 检测省略号或停顿后的修正
        if "..." in text or ".." in text:
            interruption_points += text.count("...") + text.count("..")
        
        return interruption_points / len(words) if words else 0.0
    
    def _calculate_disfluency_frequency(self, words: list, duration: float) -> float:
        """计算不流畅词频率"""
        disfluency_words = TEXT_CONFIG["disfluency_words"]
        disfluency_count = sum(1 for word in words if word.lower() in disfluency_words)
        
        if duration <= 0:
            return 0.0
        return disfluency_count / duration
    
    def _calculate_pronunciation_quality(self, asr_confidence: Optional[float], 
                                        stress_times: list, duration: float) -> float:
        """
        计算发音质量评分（L6）
        简化实现：结合ASR置信度和重音分布
        """
        score = 0.0
        
        # ASR置信度部分（60%）
        if asr_confidence is not None:
            score += asr_confidence * 0.6
        else:
            score += 0.3  # 默认中等分数
        
        # 重音分布部分（40%）
        if duration > 0 and len(stress_times) > 0:
            # 重音密度（每秒重音数）
            stress_density = len(stress_times) / duration
            # 归一化到0-1（假设正常范围是0.5-3个重音/秒）
            normalized_density = min(stress_density / 3.0, 1.0)
            score += normalized_density * 0.4
        else:
            score += 0.2  # 默认中等分数
        
        return min(score, 1.0)
    
    def normalize_features(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        归一化特征值到0-1范围
        注意：不同特征的归一化方式可能不同
        """
        normalized = {}
        
        # 定义各特征的最大值（用于归一化）
        max_values = {
            "wpsecutt": 4.0,        # 正常语速约2-3词/秒
            "wdpchk": 20.0,         # 平均语音块长度
            "wdpchkmeandev": 10.0,  # 偏差
            "conftimeavg": 1.0,     # 已经是0-1
            "repfreq": 0.2,         # 重复频率
            "silpwd": 10.0,         # 短静音次数
            "ipc": 0.3,             # 中断点频率
            "stretimemean": 2.0,     # 重音间隔（秒）
            "stresyllmdev": 1.0,    # 重音间隔偏差
            "L6": 1.0,              # 已经是0-1
            "longpfreq": 5.0,       # 长静音次数
            "dpsec": 2.0,            # 不流畅词频率
        }
        
        for key, value in features.items():
            max_val = max_values.get(key, 1.0)
            if max_val > 0:
                normalized[key] = min(value / max_val, 1.0)
            else:
                normalized[key] = 0.0
        
        return normalized
    
    def calculate_delivery_score(self, features: Dict[str, float]) -> float:
        """
        计算发音总分（加权求和）
        
        Args:
            features: 归一化后的特征字典
            
        Returns:
            发音分数（0-1，需要乘以权重后与其他部分合并）
        """
        score = 0.0
        
        for feature_name, weight in self.weights.items():
            feature_value = features.get(feature_name, 0.0)
            # 某些特征值越高越好，某些越低越好，需要调整
            if feature_name in ["repfreq", "silpwd", "ipc", "longpfreq", "dpsec", "wdpchkmeandev", "stresyllmdev"]:
                # 这些特征值越低越好，需要反转
                feature_value = 1.0 - feature_value
            
            score += feature_value * weight
        
        return score

