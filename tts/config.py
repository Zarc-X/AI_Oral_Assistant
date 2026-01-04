"""
TTS模块配置文件
适配树莓派环境的语音合成配置
"""
import os

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 模型配置
MODEL_CONFIG = {
    # Piper模型目录
    "model_dir": os.path.join(BASE_DIR, "models"),
    # 默认使用的模型 (美音女声-中等质量，平衡质量与性能)
    "default_model": "en_US-amy-medium.onnx",
    # 对应的配置文件
    "default_config": "en_US-amy-medium.onnx.json",
    # 备选模型列表
    "available_models": {
        "amy_medium": {
            "model": "en_US-amy-medium.onnx",
            "config": "en_US-amy-medium.onnx.json",
            "description": "美音女声-中等质量"
        },
        "amy_low": {
            "model": "en_US-amy-low.onnx",
            "config": "en_US-amy-low.onnx.json",
            "description": "美音女声-低质量(更快)"
        },
        "ryan_medium": {
            "model": "en_US-ryan-medium.onnx",
            "config": "en_US-ryan-medium.onnx.json",
            "description": "美音男声-中等质量"
        }
    }
}

# 音频配置
AUDIO_CONFIG = {
    # 采样率 (Piper默认22050Hz)
    "sample_rate": 22050,
    # 音频格式
    "format": "int16",
    # 声道数 (单声道)
    "channels": 1,
    # 音频缓冲区大小 (帧数)
    "buffer_size": 1024,
    # 音频块大小 (用于流式播放)
    "chunk_size": 4096,
}

# TTS引擎配置
TTS_CONFIG = {
    # 语速调节 (0.5-2.0, 1.0为正常速度)
    "speed": 1.0,
    # 是否启用流式输出
    "streaming": True,
    # 句子分割的标点符号
    "sentence_delimiters": [".", "!", "?", ";"],
    # 最大句子长度 (字符数，超过则强制分割)
    "max_sentence_length": 200,
    # 句子间停顿时间 (秒)
    "sentence_pause": 0.3,
}

# 树莓派性能优化配置
PERFORMANCE_CONFIG = {
    # 是否启用多线程合成
    "use_threading": True,
    # 合成线程数 (树莓派建议1-2)
    "num_threads": 1,
    # 音频预缓冲句子数
    "prefetch_sentences": 2,
    # 内存限制警告阈值 (MB)
    "memory_warning_threshold": 400,
}

# 日志配置
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": os.path.join(BASE_DIR, "logs", "tts.log"),
}
