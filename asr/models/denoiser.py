"""
音频去噪模块
实现谱减法和神经网络去噪算法
"""
import torch
import torchaudio
import numpy as np
import warnings

warnings.filterwarnings("ignore")


class Denoiser:
    def __init__(self, use_pretrained=True, device='cpu'):
        """
        初始化去噪模型
        
        参数:
            use_pretrained: 是否使用预训练模型
            device: 运行设备 ('cpu' 或 'cuda')
        """
        self.device = device
        self.model = None
        
        if use_pretrained:
            self._load_pretrained_model()
        else:
            self._load_lightweight_model()
    
    def _load_pretrained_model(self):
        """加载预训练模型（在树莓派上可能较慢）"""
        try:
            # 尝试加载轻量级模型
            from asteroid.models import BaseModel
            
            # 使用更轻量的模型
            model_name = "JorisCos/ConvTasNet_Libri1Mix_enhsingle_16k"
            self.model = BaseModel.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            print("加载预训练模型成功")
        except ImportError:
            print("未安装asteroid，使用传统方法")
            self._load_lightweight_model()
        except Exception as e:
            print(f"加载预训练模型失败: {e}")
            self._load_lightweight_model()
    
    def _load_lightweight_model(self):
        """加载轻量级模型（适合树莓派）"""
        # 使用传统的谱减法或维纳滤波
        print("使用轻量级去噪方法")
        self.model = "spectral_subtraction"
    
    def denoise(self, audio, sr=16000):
        """
        去噪处理
        
        参数:
            audio: 单通道音频
            sr: 采样率
            
        返回:
            去噪后的音频
        """
        if isinstance(self.model, str) and self.model == "spectral_subtraction":
            # 使用谱减法（计算量小，适合树莓派）
            return self._spectral_subtraction(audio, sr)
        else:
            # 使用神经网络模型
            return self._neural_denoise(audio, sr)
    
    def _spectral_subtraction(self, audio, sr=16000, noise_reduction=0.5):
        """
        经典谱减法
        """
        # 转换为torch张量
        if isinstance(audio, np.ndarray):
            audio_tensor = torch.FloatTensor(audio)
        else:
            audio_tensor = audio
        
        # 计算STFT
        n_fft = 512
        hop_length = 160
        window = torch.hann_window(n_fft)
        
        stft = torch.stft(audio_tensor, n_fft=n_fft, hop_length=hop_length,
                         window=window, return_complex=True)
        
        # 计算幅度谱
        magnitude = torch.abs(stft)
        phase = torch.angle(stft)
        
        # 估计噪声谱（使用前几帧）
        noise_frames = 10
        noise_estimate = torch.mean(magnitude[:, :noise_frames], dim=1, keepdim=True)
        
        # 谱减法
        enhanced_magnitude = magnitude - noise_reduction * noise_estimate
        enhanced_magnitude = torch.clamp(enhanced_magnitude, min=1e-6)
        
        # 重建复STFT
        enhanced_stft = enhanced_magnitude * torch.exp(1j * phase)
        
        # ISTFT
        enhanced_audio = torch.istft(enhanced_stft, n_fft=n_fft, hop_length=hop_length,
                                    window=window, length=len(audio_tensor))
        
        return enhanced_audio.numpy()
    
    def _neural_denoise(self, audio, sr=16000):
        """使用神经网络去噪"""
        try:
            # 转换为模型输入格式
            audio_tensor = torch.FloatTensor(audio).unsqueeze(0).to(self.device)
            
            with torch.no_grad():
                enhanced = self.model(audio_tensor)
            
            return enhanced.squeeze().cpu().numpy()
        except Exception as e:
            print(f"神经网络去噪失败: {e}")
            # 回退到谱减法
            return self._spectral_subtraction(audio, sr)