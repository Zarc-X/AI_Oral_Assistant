"""
模型下载脚本
自动下载Piper TTS模型到models目录
"""
import os
import sys
import urllib.request
import tarfile
import zipfile
import shutil
from config import BASE_DIR, MODEL_CONFIG

# Piper模型下载链接
MODEL_URLS = {
    "en_US-amy-medium": {
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json",
        "description": "美音女声-中等质量 (推荐)"
    },
    "en_US-amy-low": {
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/low/en_US-amy-low.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/low/en_US-amy-low.onnx.json",
        "description": "美音女声-低质量 (更快)"
    },
    "en_US-ryan-medium": {
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json",
        "description": "美音男声-中等质量"
    },
    "en_GB-alan-medium": {
        "url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx",
        "config_url": "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json",
        "description": "英音男声-中等质量"
    },
}


def download_file(url: str, dest_path: str, desc: str = ""):
    """下载文件，显示进度"""
    print(f"正在下载: {desc or url}")
    print(f"目标路径: {dest_path}")
    
    def show_progress(block_num, block_size, total_size):
        if total_size > 0:
            percent = min(100, block_num * block_size * 100 // total_size)
            downloaded = block_num * block_size / (1024 * 1024)
            total = total_size / (1024 * 1024)
            sys.stdout.write(f"\r进度: {percent}% ({downloaded:.1f}/{total:.1f} MB)")
            sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, dest_path, show_progress)
        print("\n下载完成!")
        return True
    except Exception as e:
        print(f"\n下载失败: {e}")
        return False


def download_model(model_key: str):
    """下载指定模型"""
    if model_key not in MODEL_URLS:
        print(f"未知模型: {model_key}")
        print(f"可用模型: {list(MODEL_URLS.keys())}")
        return False
    
    model_info = MODEL_URLS[model_key]
    model_dir = MODEL_CONFIG["model_dir"]
    
    # 确保目录存在
    os.makedirs(model_dir, exist_ok=True)
    
    # 模型文件路径
    model_filename = model_info["url"].split("/")[-1]
    config_filename = model_info["config_url"].split("/")[-1]
    
    model_path = os.path.join(model_dir, model_filename)
    config_path = os.path.join(model_dir, config_filename)
    
    # 检查是否已存在
    if os.path.exists(model_path) and os.path.exists(config_path):
        print(f"模型已存在: {model_key}")
        return True
    
    print(f"\n{'='*50}")
    print(f"下载模型: {model_key}")
    print(f"描述: {model_info['description']}")
    print(f"{'='*50}\n")
    
    # 下载模型文件
    if not os.path.exists(model_path):
        if not download_file(model_info["url"], model_path, "模型文件"):
            return False
    
    # 下载配置文件
    if not os.path.exists(config_path):
        if not download_file(model_info["config_url"], config_path, "配置文件"):
            return False
    
    print(f"\n模型 {model_key} 下载完成!")
    return True


def list_models():
    """列出可用模型"""
    print("\n可用的Piper TTS模型:")
    print("-" * 60)
    
    model_dir = MODEL_CONFIG["model_dir"]
    
    for key, info in MODEL_URLS.items():
        model_filename = info["url"].split("/")[-1]
        model_path = os.path.join(model_dir, model_filename)
        status = "已安装" if os.path.exists(model_path) else "未安装"
        print(f"[{status}] {key}: {info['description']}")
    
    print("-" * 60)


def main():
    """主函数"""
    print("=" * 50)
    print("  Piper TTS 模型下载工具")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        list_models()
        print("\n使用方法:")
        print(f"  python {sys.argv[0]} <model_key>  - 下载指定模型")
        print(f"  python {sys.argv[0]} all          - 下载所有模型")
        print(f"  python {sys.argv[0]} recommended  - 下载推荐模型")
        print("\n示例:")
        print(f"  python {sys.argv[0]} en_US-amy-medium")
        return
    
    model_key = sys.argv[1]
    
    if model_key == "all":
        print("下载所有模型...")
        for key in MODEL_URLS:
            download_model(key)
    elif model_key == "recommended":
        print("下载推荐模型 (en_US-amy-medium)...")
        download_model("en_US-amy-medium")
    else:
        download_model(model_key)
    
    print("\n" + "=" * 50)
    list_models()


if __name__ == "__main__":
    main()
