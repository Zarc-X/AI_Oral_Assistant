# 基于树莓派的英语口语训练助手

一个集成了语音合成、语音识别和评分系统的英语口语训练助手。

## 项目概述

本项目是一个完整的英语口语训练系统，基于树莓派4B实现，包含三个核心模块：

1. **语音合成模块（TTS）**：将题目文本转换为语音播放
2. **语音识别模块（ASR）**：录音并识别用户回答，包含音频增强功能
3. **评分模块**：基于TOEFL SpeechRater准则进行评分，生成中英文评价

## 项目结构

```
AI_Oral_Assistant/
├── tts/               # 语音合成模块（TTS）
│   ├── config.py
│   ├── tts_module.py
│   ├── text_processor.py
│   ├── audio_player.py
│   ├── requirements.txt
│   └── README.md
├── asr/               # 语音识别模块（ASR + 音频增强）
│   ├── config.py
│   ├── raspberry_deploy.py
│   ├── models/
│   ├── utils/
│   ├── requirements.txt
│   └── README.md
├── scoring/            # 评分模块
│   ├── config.py
│   ├── speech_rater.py
│   ├── audio_analyzer.py
│   ├── delivery_scorer.py
│   ├── language_scorer.py
│   ├── requirements.txt
│   └── README.md
├── doc/               # 文档和题库
│   ├── 大纲.txt
│   ├── question.md
│   └── 口语题库.docx
├── main.py            # 主程序入口
└── README.md          # 本文件
```

## 功能特性

### 语音合成模块（TTS）

- 基于Piper TTS引擎，支持离线运行
- 支持多种英语口音（美音/英音）
- 流式输出，低延迟
- 适配树莓派环境

**使用的模型**：

- Piper TTS模型（VITS架构）
- 预训练模型，无需训练，直接使用
- 推荐模型：en_US-amy-medium（美音女声）

**特点**：

- 完全离线运行，不依赖网络
- 模型文件较小，适合嵌入式设备
- 推理速度快，实时性好

### 语音识别模块（ASR）

- 多通道音频录音（支持6通道麦克风阵列）
- 波束形成：增强目标方向的声音
- 音频去噪：降低背景噪声
- 实时音频处理

**使用的算法/模型**：

- 波束形成：延迟求和（DSB）和MVDR算法（纯算法，无需模型）
- 音频去噪：谱减法（纯算法，默认使用）或神经网络去噪（可选预训练模型）

**特点**：

- 完全离线运行，不依赖网络
- 主要使用纯算法，计算量小
- 适配树莓派性能
- ASR功能待集成（可使用whisper或vosk等离线模型）

### 评分模块

- 发音评分：12个指标（语速、语音块、静音、重音、重复等）
- 内容评分：6个指标（词类型、词频、语法、词汇多样性等）
- 综合评价：自动生成中英文评价和建议
- 基于TOEFL SpeechRater评分准则

**使用的算法/模型**：

- 音频分析：VAD、重音检测、静音检测（纯算法，基于librosa）
- 文本分析：spaCy词性标注（可选预训练模型）、wordfreq词频分析（纯算法）
- 语言模型：可选kenlm或transformers（预训练模型，用于语法评分）

**特点**：

- 完全离线运行，不依赖网络
- 大部分功能使用纯算法，计算效率高
- 基于TOEFL官方评分准则
- 可选模型增强准确性，但不强制依赖

## 安装步骤

### 1. 系统要求

- 硬件：树莓派4B（推荐4GB内存以上）
- 系统：Raspberry Pi OS 64-bit
- Python：3.8+

### 2. 安装各模块依赖

```bash
# 安装合成模块依赖
cd tts
pip install -r requirements.txt

# 安装识别模块依赖
cd ../asr
sudo apt-get install -y portaudio19-dev python3-pyaudio
pip install -r requirements.txt

# 安装评分模块依赖
cd ../scoring
pip install -r requirements.txt

# 可选：安装spaCy英文模型（用于更准确的NLP分析）
python -m spacy download en_core_web_sm
```

### 3. 下载TTS模型

```bash
cd tts
python download_models.py en_US-amy-medium
```

### 4. 运行主程序

```bash
cd ..
python main.py
```

## 使用流程

1. **启动程序**：运行 `python main.py`
2. **开始练习**：输入 `start` 开始
3. **听题**：系统会播放题目
4. **准备**：15秒准备时间
5. **答题**：45秒答题时间（系统自动录音）
6. **评分**：系统自动评分并播放评价
7. **继续**：选择是否继续练习

## 模块说明

### 合成模块

详细文档：`tts/README.md`

主要功能：

- 文本转语音
- 流式播放
- 支持多种模型

### 识别模块

详细文档：`asr/README.md`

主要功能：

- 多通道录音
- 音频增强（波束形成+去噪）
- 音频保存

注意：目前识别模块只负责音频增强，ASR功能需要单独集成（如whisper、vosk等）。

### 评分模块

详细文档：`scoring/README.md`

主要功能：

- 18个评分指标计算
- 发音和内容分别评分
- 生成中英文评价

## 配置说明

### 题目配置

题目存储在 `question.md` 文件中，每行一道题。

### 评分权重

可以在 `scoring/config.py` 中调整各指标的权重。

### 音频配置

- 识别模块：16kHz，6通道（可在config.py中修改）
- 合成模块：22.05kHz，单声道

## 开发计划

- [ ] 集成ASR功能（whisper或vosk）
- [ ] 支持从Word文档读取题库
- [ ] 优化树莓派性能
- [ ] 添加历史记录功能
- [ ] 添加可视化界面

## 模块特性说明

### 离线运行

所有模块都支持完全离线运行，不依赖网络连接，适合树莓派部署。

### 模型和算法

- **TTS模块**：使用Piper TTS预训练模型，无需训练，直接加载使用
- **ASR模块**：主要使用纯算法（波束形成、谱减法），可选神经网络去噪模型
- **评分模块**：大部分功能使用纯算法，可选spaCy和语言模型增强准确性

### 训练和部署

- **无需训练**：所有模块都使用预训练模型或纯算法，不需要自己训练
- **无需API**：所有功能都在本地运行，不调用任何在线API

## 注意事项

1. **ASR功能**：目前识别模块的ASR功能需要集成（代码中已标注TODO）
2. **音频格式**：录音格式为16kHz单声道WAV
3. **树莓派性能**：在树莓派上运行时可能需要优化模型大小
4. **可选依赖**：spaCy和wordfreq是可选的，未安装时会使用简化方法
5. **模型下载**：TTS模块需要下载Piper模型，其他模块的模型都是可选的

## 常见问题

### Q1: 模块导入失败

确保已将所有模块路径添加到sys.path，或使用相对导入。

### Q2: 音频设备找不到

检查音频设备连接和权限，可能需要使用sudo运行。

### Q3: 评分不准确

评分基于TOEFL SpeechRater准则，可能需要根据实际情况调整权重。

## 参考资料

- Piper TTS: https://github.com/rhasspy/piper
- TOEFL SpeechRater: 见 `doc/rate.txt`
- 树莓派音频配置: https://www.raspberrypi.com/documentation/computers/configuration.html#audio-configuration
