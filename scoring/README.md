# 评分模块

基于TOEFL SpeechRater评分准则的口语评分系统。

## 功能特性

- **发音评分（Delivery）**：12个指标，包括语速、语音块、静音、重音、重复等
- **内容评分（Language Use）**：6个指标，包括词类型、词频、语法、词汇多样性等
- **综合评价**：生成中英文评价和建议

## 模块结构

```
评分/
├── config.py              # 配置文件（权重、阈值等）
├── audio_analyzer.py      # 音频分析（VAD、重音、静音检测）
├── delivery_scorer.py     # 发音评分（12个Delivery指标）
├── language_scorer.py     # 内容评分（6个Language Use指标）
├── score_calculator.py    # 分数计算和加权
├── feedback_generator.py # 评价生成（中英文）
├── speech_rater.py        # 评分模块主类和接口
└── requirements.txt       # 依赖包
```

## 安装依赖

```bash
pip install -r requirements.txt

# 可选：安装spaCy英文模型（用于更准确的NLP分析）
python -m spacy download en_core_web_sm
```

## 使用方法

### 基本使用

```python
from speech_rater import SpeechRater

# 初始化评分器
rater = SpeechRater()

# 评分
result = rater.score(
    audio_path="recorded_audio.wav",
    text="I think the most important quality for a friend is honesty.",
    asr_confidence=0.85,  # 可选
    task_type="independent"
)

# 获取结果
print(f"总分: {result.raw_score:.2f} / 4.0")
print(f"发音分: {result.delivery_score:.2f} / 4.0")
print(f"内容分: {result.language_score:.2f} / 4.0")
print(f"英文评价: {result.feedback_en}")
print(f"中文评价: {result.feedback_zh}")
```

## 评分指标

### 发音指标（Delivery Features）

| 指标          | 权重 | 说明                 |
| ------------- | ---- | -------------------- |
| wpsecutt      | 15%  | 语速（每秒单词数）   |
| stretimemean  | 15%  | 重音音节平均距离     |
| wdpchk        | 13%  | 平均语音块长度       |
| wdpchkmeandev | 13%  | 语音块长度偏差       |
| conftimeavg   | 12%  | ASR置信度            |
| repfreq       | 8%   | 重复频率             |
| silpwd        | 6%   | 短静音频率（>0.15s） |
| ipc           | 6%   | 中断点频率           |
| stresyllmdev  | 5%   | 重音音节距离偏差     |
| L6            | 3%   | 发音质量评分         |
| longpfreq     | 3%   | 长静音频率（>0.5s）  |
| dpsec         | 1%   | 不流畅词频率         |

### 内容指标（Language Use Features）

| 指标      | 权重 | 说明           |
| --------- | ---- | -------------- |
| types     | 35%  | 词类型数量     |
| poscvamax | 18%  | POS bigram对比 |
| logfreq   | 15%  | 词汇频率       |
| lmscore   | 11%  | 语言模型分数   |
| tpsec     | 11%  | 每秒词类型数   |
| cvamax    | 10%  | 单词数对比     |

## 注意事项

1. **音频格式**：支持WAV格式，采样率16kHz，单声道
2. **可选依赖**：spaCy和wordfreq是可选的，未安装时会使用简化方法
3. **性能**：在树莓派上运行可能需要优化，建议使用轻量级模型

## 配置说明

可以在 `config.py` 中调整：

- 评分权重
- 音频分析参数
- 静音检测阈值
- 重音检测参数
- 文本分析参数
