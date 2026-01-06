"""
语音识别模块 - 树莓派部署
负责录音、音频增强（波束形成+去噪）和音频保存
"""
import numpy as np
import pyaudio
import wave
import time
import threading
import queue
import logging
import os
from .models.beamformer import Beamformer
from .models.denoiser import Denoiser
from .config import Config
import warnings
warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)


class RaspberryPiAudioProcessor:
    """树莓派音频处理类"""
    
    def __init__(self):
        # 音频参数
        self.channels = Config.CHANNELS
        self.sample_rate = Config.SAMPLE_RATE
        self.chunk_size = Config.CHUNK_SIZE
        self.format = pyaudio.paInt16
        
        # 初始化PyAudio
        self.p = pyaudio.PyAudio()
        
        # 初始化模型
        logger.info("初始化语音增强模型...")
        self.beamformer = Beamformer(
            mic_positions=Config.MIC_POSITIONS,
            fs=self.sample_rate,
            direction=Config.LOOK_DIRECTION
        )
        
        self.denoiser = Denoiser(
            use_pretrained=Config.USE_PRETRAINED,
            device='cpu'
        )
        
        # 音频缓冲区
        self.audio_buffer = queue.Queue(maxsize=100)
        
        # 控制标志
        self.is_recording = False
        self.is_processing = False
        
        # 输出音频路径
        self.output_audio_path = "raspberry_output.wav"
        
        logger.info("树莓派音频处理器初始化完成")
    
    def list_audio_devices(self):
        """
        列出可用音频设备
        
        Returns:
            设备列表
        """
        logger.info("列出可用音频设备...")
        devices = []
        for i in range(self.p.get_device_count()):
            dev_info = self.p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] >= self.channels:
                device_info = {
                    'index': i,
                    'name': dev_info['name'],
                    'channels': dev_info['maxInputChannels'],
                    'sample_rate': dev_info['defaultSampleRate']
                }
                devices.append(device_info)
                logger.info(f"设备 [{i}]: {dev_info['name']}, 通道: {dev_info['maxInputChannels']}, 采样率: {dev_info['defaultSampleRate']}")
        
        return devices
    
    def find_6ch_device(self):
        """
        查找6通道麦克风设备
        
        Returns:
            设备索引，如果未找到返回None
        """
        for i in range(self.p.get_device_count()):
            dev_info = self.p.get_device_info_by_index(i)
            if dev_info['maxInputChannels'] >= self.channels:
                logger.info(f"找到多通道设备: {dev_info['name']}")
                return i
        
        logger.warning("未找到6通道麦克风设备，使用默认设备")
        return None
    
    def record_callback(self, in_data, frame_count, time_info, status):
        """录音回调函数"""
        if self.is_recording:
            # 将数据放入队列
            data = np.frombuffer(in_data, dtype=np.int16)
            # 重新整形为多通道
            data = data.reshape(-1, self.channels).T  # 转换为(channels, samples)
            
            if not self.audio_buffer.full():
                self.audio_buffer.put(data)
        
        return (None, pyaudio.paContinue)
    
    def start_recording(self, device_index=None, duration=None):
        """
        开始录音
        
        Args:
            device_index: 音频设备索引，None则自动查找
            duration: 录音时长（秒），None则手动停止
        """
        logger.info("开始录音...")
        
        if device_index is None:
            device_index = self.find_6ch_device()
        
        # 打开音频流
        stream = self.p.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            input_device_index=device_index,
            stream_callback=self.record_callback
        )
        
        self.is_recording = True
        
        # 启动处理线程
        process_thread = threading.Thread(target=self.process_audio)
        process_thread.daemon = True
        process_thread.start()
        
        if duration:
            # 定时停止
            time.sleep(duration)
            self.stop_recording(stream)
        else:
            # 等待用户停止
            input("按Enter键停止录音...")
            self.stop_recording(stream)
    
    def stop_recording(self, stream):
        """
        停止录音
        
        Args:
            stream: PyAudio流对象
        """
        logger.info("停止录音...")
        self.is_recording = False
        time.sleep(0.5)  # 等待缓冲区处理完成
        stream.stop_stream()
        stream.close()
    
    def process_audio(self):
        """
        处理音频数据（在独立线程中运行）
        执行波束形成和去噪处理
        """
        self.is_processing = True
        
        logger.info("开始实时处理音频...")
        
        # 保存处理结果的缓冲区
        output_buffer = []
        
        while self.is_recording or not self.audio_buffer.empty():
            try:
                # 从队列获取数据
                chunk = self.audio_buffer.get(timeout=0.5)
                
                # 1. 波束形成
                enhanced = self.beamformer.delay_and_sum(chunk)
                
                # 2. 去噪
                final = self.denoiser.denoise(enhanced, self.sample_rate)
                
                # 保存结果
                output_buffer.append(final)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"处理音频时出错: {e}")
                continue
        
        # 保存处理后的音频
        if output_buffer:
            final_audio = np.concatenate(output_buffer)
            self.save_audio(final_audio, self.output_audio_path)
            logger.info(f"音频已保存到: {self.output_audio_path}")
        
        self.is_processing = False
        logger.info("音频处理完成")
    
    def save_audio(self, audio, filename):
        """
        保存音频文件
        
        Args:
            audio: 音频数据（numpy数组）
            filename: 输出文件名
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
            
            # 转换为16位整数
            audio_int16 = (audio * 32767).astype(np.int16)
            
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(1)  # 单通道输出
                wf.setsampwidth(2)  # 2字节 = 16位
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_int16.tobytes())
            
            logger.info(f"音频已保存: {filename}")
        except Exception as e:
            logger.error(f"保存音频失败: {e}")
            raise
    
    def cleanup(self):
        """清理资源"""
        try:
            self.p.terminate()
            logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时出错: {e}")

def main():
    """主函数 - 用于独立测试"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    logger.info("=" * 50)
    logger.info("树莓派语音增强系统部署")
    logger.info("=" * 50)
    
    # 创建处理器实例
    processor = RaspberryPiAudioProcessor()
    
    try:
        # 显示设备列表
        processor.list_audio_devices()
        
        # 开始录音（默认设备，录音10秒）
        processor.start_recording(duration=10)
        
    except KeyboardInterrupt:
        logger.info("用户中断")
    except Exception as e:
        logger.error(f"运行错误: {e}")
    finally:
        processor.cleanup()

if __name__ == "__main__":
    main()