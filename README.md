# 树莓派英语口语练习助手

基于树莓派的英语口语训练系统，集成语音合成、语音识别和智能评分功能。

## 功能特性

- **语音合成（TTS）**：将题目文本转换为语音播放
- **语音识别（ASR）**：录音并识别用户回答，支持音频增强
- **智能评分**：基于TOEFL SpeechRater准则进行评分，生成中英文评价

## 系统要求

- 硬件：树莓派4B（推荐4GB内存以上）
- 系统：Raspberry Pi OS 64-bit
- Python：3.9（通过conda管理）
- 已安装：conda（Miniconda或Anaconda）

## 快速安装

### 一键安装（推荐）

```bash
cd /home/pi/Desktop/AI_Oral_Assistant
./install.sh
```

### 手动安装

如果自动安装失败，可以手动执行：

```bash
# 1. 安装系统依赖
sudo apt-get update
sudo apt-get install -y portaudio19-dev python3-pyaudio ffmpeg gfortran build-essential

# 2. 创建conda环境
conda env create -f environment.yml
conda activate oral_assistant

# 3. 安装Python依赖
cd tts && pip install -r requirements.txt && cd ..
cd asr && pip install numpy scipy soundfile librosa matplotlib pyaudio sounddevice && cd ..
cd scoring && pip install numpy scipy librosa soundfile wordfreq nltk && cd ..

# 4. 下载TTS模型
cd tts && python download_models.py en_US-amy-medium && cd ..
```

## 使用方法

### 启动程序

```bash
conda activate oral_assistant
cd /home/pi/Desktop/AI_Oral_Assistant
python main.py
```

### 使用流程

1. **启动程序**：运行 `python main.py`
2. **开始练习**：输入 `start` 开始
3. **听题**：系统会播放题目
4. **准备**：15秒准备时间
5. **答题**：45秒答题时间（系统自动录音）
6. **评分**：系统自动评分并播放评价
7. **继续**：选择是否继续练习

## 项目结构

```
AI_Oral_Assistant/
├── tts/               # 语音合成模块
│   ├── tts_module.py  # TTS核心模块
│   ├── config.py      # 配置文件
│   └── models/        # TTS模型目录
├── asr/               # 语音识别模块
│   ├── raspberry_deploy.py  # 树莓派部署
│   ├── models/        # 音频处理模型
│   └── utils/         # 工具函数
├── scoring/           # 评分模块
│   ├── speech_rater.py      # 评分主类
│   ├── audio_analyzer.py    # 音频分析
│   ├── delivery_scorer.py  # 发音评分
│   └── language_scorer.py  # 内容评分
├── doc/               # 文档和题库
├── main.py            # 主程序入口
├── install.sh         # 安装脚本
├── environment.yml    # Conda环境配置
└── README.md          # 本文件
```

## 配置说明

### 题目配置

题目存储在 `question.md` 文件中，每行一道题。

### 评分权重

可以在 `scoring/config.py` 中调整各指标的权重。

### 音频配置

- 识别模块：16kHz，6通道（可在 `asr/config.py` 中修改）
- 合成模块：22.05kHz，单声道

## 常见问题

### Q1: conda命令未找到

```bash
# 初始化conda
source ~/miniconda3/etc/profile.d/conda.sh
# 或
source ~/anaconda3/etc/profile.d/conda.sh

# 添加到 ~/.bashrc
echo "source ~/miniconda3/etc/profile.d/conda.sh" >> ~/.bashrc
```

### Q2: 环境使用了PyPy而不是CPython

```bash
# 删除环境重新创建
conda env remove -n oral_assistant -y
./install.sh
```

### Q3: TTS模型下载失败

手动下载：
1. 访问 https://github.com/rhasspy/piper/releases
2. 下载 `en_US-amy-medium.onnx` 和 `en_US-amy-medium.onnx.json`
3. 放到 `tts/models/` 目录

### Q4: 音频设备权限问题

```bash
sudo usermod -a -G audio $USER
# 重新登录后生效
```

### Q5: 某些包安装失败

以下包是可选的，不影响基本功能：
- `spacy` - 评分功能会使用简化方法
- `torch` - ASR模块不使用（树莓派不支持）

## 技术说明

### 离线运行

所有模块都支持完全离线运行，不依赖网络连接。

### 模型和算法

- **TTS模块**：使用Piper TTS预训练模型
- **ASR模块**：主要使用纯算法（波束形成、谱减法）
- **评分模块**：大部分功能使用纯算法，可选spaCy增强

### 性能优化

- 适配树莓派ARM架构
- 使用轻量级算法，减少计算量
- 支持流式处理，降低延迟

## 开发计划

- [ ] 集成ASR功能（whisper或vosk）
- [ ] 支持从Word文档读取题库
- [ ] 添加历史记录功能
- [ ] 添加可视化界面

## 许可证

本项目仅供学习和研究使用。

## 参考资料

- Piper TTS: https://github.com/rhasspy/piper
- TOEFL SpeechRater: 见 `doc/rate.txt`
- 树莓派音频配置: https://www.raspberrypi.com/documentation/computers/configuration.html#audio-configuration
