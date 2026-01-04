"""
音频播放器模块
负责音频数据的播放和管理，适配树莓派硬件
"""
import threading
import queue
import time
import logging
from typing import Optional, Callable
import numpy as np

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

from config import AUDIO_CONFIG, PERFORMANCE_CONFIG

logger = logging.getLogger(__name__)


class AudioPlayer:
    """
    音频播放器类
    支持流式播放和播放控制
    """
    
    def __init__(self, sample_rate: int = None, channels: int = None):
        """
        初始化音频播放器
        
        Args:
            sample_rate: 采样率，默认从配置读取
            channels: 声道数，默认从配置读取
        """
        self.sample_rate = sample_rate or AUDIO_CONFIG["sample_rate"]
        self.channels = channels or AUDIO_CONFIG["channels"]
        self.chunk_size = AUDIO_CONFIG["chunk_size"]
        
        # 播放状态
        self._is_playing = False
        self._stop_flag = threading.Event()
        self._pause_flag = threading.Event()
        
        # 音频队列
        self._audio_queue = queue.Queue()
        self._play_thread: Optional[threading.Thread] = None
        
        # 播放完成回调
        self._on_complete: Optional[Callable] = None
        
        # 选择可用的音频后端
        self._backend = self._select_backend()
        
        # PyAudio实例
        self._pyaudio_instance = None
        self._stream = None
    
    def _select_backend(self) -> str:
        """选择可用的音频后端"""
        if SOUNDDEVICE_AVAILABLE:
            logger.info("使用 sounddevice 后端")
            return "sounddevice"
        elif PYAUDIO_AVAILABLE:
            logger.info("使用 pyaudio 后端")
            return "pyaudio"
        else:
            logger.warning("未找到音频后端，将使用模拟模式")
            return "dummy"
    
    def _init_pyaudio(self):
        """初始化PyAudio"""
        if self._pyaudio_instance is None and PYAUDIO_AVAILABLE:
            self._pyaudio_instance = pyaudio.PyAudio()
    
    def _close_pyaudio(self):
        """关闭PyAudio"""
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
        if self._pyaudio_instance:
            self._pyaudio_instance.terminate()
            self._pyaudio_instance = None
    
    def play(self, audio_data: np.ndarray, blocking: bool = True):
        """
        播放音频数据
        
        Args:
            audio_data: numpy数组格式的音频数据
            blocking: 是否阻塞等待播放完成
        """
        if audio_data is None or len(audio_data) == 0:
            logger.warning("音频数据为空，跳过播放")
            return
        
        # 确保数据类型正确
        if audio_data.dtype != np.int16:
            if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                audio_data = (audio_data * 32767).astype(np.int16)
            else:
                audio_data = audio_data.astype(np.int16)
        
        self._stop_flag.clear()
        self._is_playing = True
        
        try:
            if self._backend == "sounddevice":
                self._play_sounddevice(audio_data, blocking)
            elif self._backend == "pyaudio":
                self._play_pyaudio(audio_data, blocking)
            else:
                self._play_dummy(audio_data, blocking)
        except Exception as e:
            logger.error(f"播放出错: {e}")
            self._is_playing = False
            raise
    
    def _play_sounddevice(self, audio_data: np.ndarray, blocking: bool):
        """使用sounddevice播放"""
        try:
            sd.play(audio_data, samplerate=self.sample_rate)
            if blocking:
                sd.wait()
                self._is_playing = False
                if self._on_complete:
                    self._on_complete()
        except Exception as e:
            logger.error(f"sounddevice播放失败: {e}")
            raise
    
    def _play_pyaudio(self, audio_data: np.ndarray, blocking: bool):
        """使用pyaudio播放"""
        self._init_pyaudio()
        
        try:
            self._stream = self._pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size
            )
            
            # 分块播放
            audio_bytes = audio_data.tobytes()
            chunk_bytes = self.chunk_size * 2  # int16 = 2 bytes
            
            for i in range(0, len(audio_bytes), chunk_bytes):
                if self._stop_flag.is_set():
                    break
                
                # 暂停检查
                while self._pause_flag.is_set() and not self._stop_flag.is_set():
                    time.sleep(0.1)
                
                chunk = audio_bytes[i:i + chunk_bytes]
                self._stream.write(chunk)
            
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None
            
            self._is_playing = False
            if self._on_complete and not self._stop_flag.is_set():
                self._on_complete()
                
        except Exception as e:
            logger.error(f"pyaudio播放失败: {e}")
            raise
    
    def _play_dummy(self, audio_data: np.ndarray, blocking: bool):
        """模拟播放（无音频输出）"""
        duration = len(audio_data) / self.sample_rate
        logger.info(f"[模拟播放] 时长: {duration:.2f}秒")
        
        if blocking:
            time.sleep(duration)
            self._is_playing = False
            if self._on_complete:
                self._on_complete()
    
    def play_stream(self, audio_generator, blocking: bool = True):
        """
        流式播放音频
        
        Args:
            audio_generator: 音频数据生成器
            blocking: 是否阻塞
        """
        self._stop_flag.clear()
        self._is_playing = True
        
        def _stream_play():
            try:
                for audio_chunk in audio_generator:
                    if self._stop_flag.is_set():
                        break
                    self.play(audio_chunk, blocking=True)
            finally:
                self._is_playing = False
                if self._on_complete:
                    self._on_complete()
        
        if blocking:
            _stream_play()
        else:
            self._play_thread = threading.Thread(target=_stream_play)
            self._play_thread.daemon = True
            self._play_thread.start()
    
    def stop(self):
        """停止播放"""
        self._stop_flag.set()
        self._pause_flag.clear()
        
        if self._backend == "sounddevice" and SOUNDDEVICE_AVAILABLE:
            sd.stop()
        
        if self._stream:
            try:
                self._stream.stop_stream()
            except:
                pass
        
        # 等待播放线程结束
        if self._play_thread and self._play_thread.is_alive():
            self._play_thread.join(timeout=1.0)
        
        self._is_playing = False
        logger.info("播放已停止")
    
    def pause(self):
        """暂停播放"""
        if self._is_playing:
            self._pause_flag.set()
            if self._backend == "sounddevice" and SOUNDDEVICE_AVAILABLE:
                sd.stop()
            logger.info("播放已暂停")
    
    def resume(self):
        """恢复播放"""
        self._pause_flag.clear()
        logger.info("播放已恢复")
    
    @property
    def is_playing(self) -> bool:
        """返回当前是否正在播放"""
        return self._is_playing
    
    def set_on_complete(self, callback: Callable):
        """设置播放完成回调"""
        self._on_complete = callback
    
    def list_devices(self):
        """列出可用的音频设备"""
        devices = []
        
        if SOUNDDEVICE_AVAILABLE:
            try:
                device_list = sd.query_devices()
                for i, dev in enumerate(device_list):
                    if dev['max_output_channels'] > 0:
                        devices.append({
                            'id': i,
                            'name': dev['name'],
                            'channels': dev['max_output_channels'],
                            'sample_rate': dev['default_samplerate']
                        })
            except Exception as e:
                logger.error(f"查询设备失败: {e}")
        
        elif PYAUDIO_AVAILABLE:
            self._init_pyaudio()
            try:
                for i in range(self._pyaudio_instance.get_device_count()):
                    dev = self._pyaudio_instance.get_device_info_by_index(i)
                    if dev['maxOutputChannels'] > 0:
                        devices.append({
                            'id': i,
                            'name': dev['name'],
                            'channels': dev['maxOutputChannels'],
                            'sample_rate': dev['defaultSampleRate']
                        })
            except Exception as e:
                logger.error(f"查询设备失败: {e}")
        
        return devices
    
    def __del__(self):
        """析构函数，清理资源"""
        self.stop()
        self._close_pyaudio()


def test_player():
    """测试音频播放器"""
    player = AudioPlayer()
    
    print("=== 音频播放器测试 ===\n")
    
    # 列出设备
    print("可用音频设备:")
    devices = player.list_devices()
    for dev in devices:
        print(f"  [{dev['id']}] {dev['name']} (通道: {dev['channels']})")
    
    # 生成测试音频 (440Hz正弦波)
    print("\n生成测试音频 (440Hz, 2秒)...")
    duration = 2.0
    t = np.linspace(0, duration, int(player.sample_rate * duration), dtype=np.float32)
    audio = (np.sin(2 * np.pi * 440 * t) * 0.5 * 32767).astype(np.int16)
    
    print("播放测试音频...")
    player.play(audio, blocking=True)
    print("播放完成!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_player()
