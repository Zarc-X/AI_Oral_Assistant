# 快速开始

## 安装（3步）

```bash
# 1. 进入项目目录
cd /home/pi/Desktop/AI_Oral_Assistant

# 2. 运行安装脚本
./install.sh

# 3. 激活环境并运行
conda activate oral_assistant
python main.py
```

## 使用

1. 运行程序后，输入 `start` 开始练习
2. 听题目（系统自动播放）
3. 15秒准备时间
4. 45秒答题时间（自动录音）
5. 查看评分结果

## 常见问题速查

| 问题 | 解决方案 |
|------|---------|
| conda未找到 | `source ~/miniforge3/etc/profile.d/conda.sh` |
| PyPy问题 | 删除环境：`conda env remove -n oral_assistant -y` 然后重新运行 `./install.sh` |
| TTS模型缺失 | `cd tts && python download_models.py en_US-amy-medium` |
| 音频权限 | `sudo usermod -a -G audio $USER` 然后重新登录 |

## 详细文档

查看 `README.md` 获取完整文档。
