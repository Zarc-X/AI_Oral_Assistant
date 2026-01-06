"""
评分模块
基于TOEFL SpeechRater评分准则的口语评分系统
"""
from .speech_rater import SpeechRater, ScoreResult

__all__ = ["SpeechRater", "ScoreResult"]

