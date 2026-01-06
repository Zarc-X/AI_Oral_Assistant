#!/bin/bash
# 树莓派口语练习助手 - 环境安装脚本

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "树莓派口语练习助手 - 环境安装"
echo "=========================================="
echo ""

# 检查conda
if ! command -v conda &> /dev/null; then
    echo "错误: 未找到conda，请先安装conda"
    echo "访问: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

source "$(conda info --base)/etc/profile.d/conda.sh"

# 步骤1: 安装系统依赖
echo " 步骤 1/5: 安装系统依赖..."
sudo apt-get update -qq
sudo apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg \
    gfortran \
    build-essential \
    > /dev/null 2>&1
echo "✓ 系统依赖安装完成"

# 步骤2: 清理旧环境
echo ""
echo " 步骤 2/5: 清理旧环境..."
if conda env list | grep -q "^oral_assistant "; then
    conda env remove -n oral_assistant -y > /dev/null 2>&1
    echo "✓ 已删除旧环境"
else
    echo "✓ 无需清理"
fi

# 步骤3: 创建conda环境
echo ""
echo " 步骤 3/5: 创建conda环境..."
# 先创建基础环境，确保使用CPython
conda create -n oral_assistant python=3.9.23 -y --no-default-packages > /dev/null 2>&1
# 安装基础包（使用conda安装，避免编译问题）
conda activate oral_assistant
conda install -n oral_assistant -c conda-forge -y \
    pip \
    numpy=1.26.* \
    scipy=1.11.* \
    pandas \
    matplotlib \
    ffmpeg \
    > /dev/null 2>&1

# 验证Python类型
conda activate oral_assistant
PYTHON_TYPE=$(python -c "import sys; print('PyPy' if hasattr(sys, 'pypy_version_info') else 'CPython')" 2>/dev/null)
if [ "$PYTHON_TYPE" = "PyPy" ]; then
    echo "  警告: 检测到PyPy，正在修复..."
    conda install -n oral_assistant python=3.9.23=*_cpython -y --force-reinstall > /dev/null 2>&1
    PYTHON_TYPE=$(python -c "import sys; print('PyPy' if hasattr(sys, 'pypy_version_info') else 'CPython')" 2>/dev/null)
    if [ "$PYTHON_TYPE" = "PyPy" ]; then
        echo " 错误: 无法修复PyPy问题"
        exit 1
    fi
fi
echo "✓ 环境创建完成: $(python --version) ($PYTHON_TYPE)"

# 步骤4: 安装Python依赖
echo ""
echo " 步骤 4/5: 安装Python依赖..."

# TTS模块
echo "  - TTS模块..."
cd tts
pip install -q -r requirements.txt > /dev/null 2>&1 || {
    echo "      部分依赖安装失败，但会继续"
}
cd ..

# ASR模块
echo "  - ASR模块..."
cd asr
pip install -q numpy scipy soundfile librosa matplotlib pyaudio sounddevice > /dev/null 2>&1 || {
    echo "      部分依赖安装失败，但会继续"
}
cd ..

# 评分模块
echo "  - 评分模块..."
cd scoring
pip install -q numpy scipy librosa soundfile wordfreq nltk > /dev/null 2>&1 || {
    echo "     部分依赖安装失败，但会继续"
}
cd ..

echo "✓ Python依赖安装完成"

# 步骤5: 下载TTS模型
echo ""
echo " 步骤 5/5: 下载TTS模型..."
cd tts
if [ -f "download_models.py" ]; then
    python download_models.py en_US-amy-medium > /dev/null 2>&1 || {
        echo "    模型下载失败，可稍后运行: cd tts && python download_models.py en_US-amy-medium"
    }
else
    echo "    未找到download_models.py"
fi
cd ..

# 创建必要目录
mkdir -p tts/models tts/logs asr/logs asr/models scoring/logs scoring/models

echo ""
echo "=========================================="
echo " 安装完成！"
echo "=========================================="
echo ""
echo "使用方法:"
echo "  1. 激活环境: conda activate oral_assistant"
echo "  2. 进入目录: cd $SCRIPT_DIR"
echo "  3. 运行程序: python main.py"
echo ""
echo "提示:"
echo "  - 如果TTS模型未下载，运行: cd tts && python download_models.py en_US-amy-medium"
echo "  - 查看详细文档: cat README.md"
echo ""

