# 语音合成模块

基于树莓派的语音合成（TTS）模块，负责将文本转换为自然流畅的语音输出。

## 功能特性

- 高质量语音：基于Piper TTS引擎，支持多种英语口音（美音/英音）
- 树莓派优化：专为嵌入式设备优化，低内存占用，快速推理
- 流式输出：支持边合成边播放，减少响应延迟
- 离线运行：无需网络连接，满足课程实验要求
- 备选方案：提供Edge-TTS在线备选，音质更佳

## 模块结构

```
合成/
├── config.py              # 配置文件
├── text_processor.py      # 文本预处理（数字转换、分句等）
├── audio_player.py        # 音频播放器（支持sounddevice/pyaudio）
├── tts_module.py          # TTS核心模块（封装Piper引擎）
├── main.py                # 主程序入口（交互/命令行模式）
├── edge_tts_fallback.py   # Edge-TTS在线备选方案
├── download_models.py     # 模型下载脚本
├── requirements.txt       # Python依赖
├── README.md              # 本文档
├── models/                # 模型目录（需下载模型）
└── logs/                  # 日志目录
```

## 安装依赖

```bash
# 安装系统依赖（树莓派）
sudo apt update && sudo apt upgrade -y
sudo apt install -y portaudio19-dev python3-pyaudio alsa-utils

# 安装Python依赖
pip install -r requirements.txt

# 下载Piper模型
python download_models.py en_US-amy-medium
```

## 使用方法

### 命令行使用

```bash
# 交互模式
python main.py

# 直接合成文本
python main.py -t "Hello, how are you today?"

# 从文件读取
python main.py -f input.txt

# 运行测试
python main.py --test

# 列出音频设备
python main.py --list-devices
```

### Python API调用

```python
from tts_module import TextToSpeech

# 创建TTS实例
tts = TextToSpeech()

# 基本使用：合成并播放
tts.speak("Hello, how are you today?")

# 异步播放（不阻塞主线程）
tts.speak("This is a long sentence.", blocking=False)

# 检查状态
if tts.is_speaking:
    print("正在播放中...")

# 停止播放
tts.stop()

# 仅合成不播放
audio_data = tts.synthesize("Hello world")
```

### 与主程序集成

在主程序中使用：

```python
from 合成.tts_module import TextToSpeech

tts = TextToSpeech()
tts.speak("Please start your answer now.", blocking=True)
```

## 配置说明

在 `config.py` 中可以配置：

- **模型配置**：模型路径、默认模型、可用模型列表
- **音频配置**：采样率、格式、声道数、缓冲区大小
- **TTS引擎配置**：语速、流式输出、分句设置
- **性能优化配置**：多线程、预缓冲、内存限制

### 模型选择

推荐模型：
- `en_US-amy-medium`: 美音女声，中等质量（推荐）
- `en_US-ryan-medium`: 美音男声，中等质量
- `en_US-amy-low`: 美音女声，低质量（更快，适合性能较低的设备）

## 模块说明

### TextToSpeech

主TTS类，提供以下方法：

- `__init__(model_name, auto_load)`: 初始化TTS
- `load_model(model_name)`: 加载模型
- `synthesize(text)`: 合成音频（返回numpy数组）
- `speak(text, blocking)`: 合成并播放
- `speak_stream(generator, blocking)`: 流式合成播放
- `stop()`: 停止播放
- `set_speed(speed)`: 设置语速(0.5-2.0)
- `set_callbacks(...)`: 设置回调函数

### TextProcessor

文本预处理模块：

- 文本正则化（数字、货币、缩写转换）
- 智能分句（按标点符号分割长文本）
- 特殊字符清理

### AudioPlayer

音频播放器模块：

- 支持sounddevice和pyaudio两种后端
- 流式播放支持
- 播放控制（暂停/恢复/停止）

### EdgeTTSFallback

在线备选方案：

- 基于微软Edge TTS API
- 需要网络连接
- 音质更好，但有延迟

## 树莓派硬件配置

### 音频输出选择

推荐使用USB声卡，树莓派自带3.5mm接口底噪较大。

```bash
# 查看音频设备
aplay -l

# 测试音频输出
speaker-test -t wav -c 2

# 配置音频输出
sudo raspi-config
# 选择 System Options -> Audio -> 选择输出设备
```

### 性能优化

```bash
# 监控CPU温度（防止过热降频）
vcgencmd measure_temp

# 查看内存使用
free -h

# 调整进程优先级（可选）
nice -n -10 python main.py
```

## 常见问题

### Q1: 模型加载失败

错误信息：`模型文件不存在: models/en_US-amy-medium.onnx`

解决方法：下载Piper模型到`models`目录。访问 https://github.com/rhasspy/piper/blob/master/VOICES.md

### Q2: 没有声音输出

检查步骤：
```bash
# 检查音频设备
aplay -l
speaker-test -t wav

# 确认音量
alsamixer
```

### Q3: 播放卡顿

解决方法：
- 使用`low`质量版本的模型（如`en_US-amy-low`）
- 检查CPU温度是否过高
- 减少后台进程

### Q4: ImportError: No module named 'piper'

解决方法：
```bash
pip install piper-tts
```

### Q5: 如何在没有树莓派的情况下测试？

在Windows/Mac上可以正常运行和测试，只是最终部署需要在树莓派上。

## 扩展和定制

### 添加新模型

1. 从Piper仓库下载模型文件
2. 放入`models/`目录
3. 在`config.py`的`available_models`中添加配置

### 自定义语速

```python
tts = TextToSpeech()
tts.set_speed(1.2)  # 加快20%
tts.set_speed(0.8)  # 减慢20%
```

### 修改分句策略

编辑`config.py`中的`TTS_CONFIG`:
```python
TTS_CONFIG = {
    "sentence_delimiters": [".", "!", "?", ";"],
    "max_sentence_length": 200,
    "sentence_pause": 0.3,
}
```

## 接口文档

### TextToSpeech 类

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `__init__(model_name, auto_load)` | model_name: str, auto_load: bool | - | 初始化TTS |
| `load_model(model_name)` | model_name: str | bool | 加载模型 |
| `synthesize(text)` | text: str | np.ndarray | 合成音频 |
| `speak(text, blocking)` | text: str, blocking: bool | - | 合成并播放 |
| `speak_stream(generator, blocking)` | generator, blocking: bool | - | 流式合成播放 |
| `stop()` | - | - | 停止播放 |
| `is_speaking` | - | bool | 是否正在播放 |
| `is_loaded` | - | bool | 模型是否已加载 |
| `set_speed(speed)` | speed: float | - | 设置语速(0.5-2.0) |
| `set_callbacks(...)` | on_start, on_complete, on_sentence | - | 设置回调 |

## 参考资料

- Piper TTS GitHub: https://github.com/rhasspy/piper
- Piper模型下载: https://github.com/rhasspy/piper/blob/master/VOICES.md
- Edge-TTS: https://github.com/rany2/edge-tts
- 树莓派音频配置: https://www.raspberrypi.com/documentation/computers/configuration.html#audio-configuration
