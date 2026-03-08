"""
声学 VAD (Voice Activity Detection)
使用 WebRTC VAD 检测音频中是否有人声
"""
import collections
import numpy as np
from typing import Generator, Tuple
from loguru import logger

# 兼容 Python 3.14+ (pkg_resources removed)
try:
    import webrtcvad
except ImportError:
    # 如果没有 webrtcvad，使用简单的能量检测作为后备
    webrtcvad = None


class AcousticVAD:
    """声学语音活动检测"""
    
    def __init__(self, sample_rate: int = 16000, aggressiveness: int = 2):
        """
        初始化声学 VAD
        
        Args:
            sample_rate: 采样率 (Hz)，支持 8000/16000/32000/48000
            aggressiveness: 敏感度 (0-3)，越高越敏感
        """
        self.sample_rate = sample_rate
        self.aggressiveness = aggressiveness
        
        # 帧大小 (ms)
        self.frame_duration_ms = 30
        self.frame_size = int(sample_rate * self.frame_duration_ms / 1000)
        
        # 滑动窗口用于平滑检测
        self.window_size = 10  # 10 帧
        self.window = collections.deque(maxlen=self.window_size)
        
        # 初始化 WebRTC VAD（如果可用）
        if webrtcvad:
            self.vad = webrtcvad.Vad(aggressiveness)
            self.use_webrtc = True
            logger.info(f"AcousticVAD initialized with WebRTC VAD: sample_rate={sample_rate}")
        else:
            self.vad = None
            self.use_webrtc = False
            # 能量阈值（简单 VAD 用）
            self.energy_threshold = 1000
            logger.info(f"AcousticVAD initialized with simple energy VAD: sample_rate={sample_rate}")
    
    def is_speech(self, frame: bytes) -> bool:
        """
        检测单帧是否包含语音
        
        Args:
            frame: 音频帧 (16-bit PCM)
            
        Returns:
            bool: 是否包含语音
        """
        try:
            if self.use_webrtc and self.vad:
                is_speech = self.vad.is_speech(frame, self.sample_rate)
            else:
                # 简单能量检测
                audio_array = np.frombuffer(frame, dtype=np.int16)
                energy = np.sum(np.abs(audio_array))
                is_speech = energy > self.energy_threshold * len(audio_array)
            
            self.window.append(is_speech)
            
            # 使用滑动窗口平滑结果（超过 50% 的帧判定为语音）
            return sum(self.window) > len(self.window) / 2
        except Exception as e:
            logger.warning(f"VAD error: {e}")
            return False
    
    def process_audio(self, audio_data: np.ndarray) -> Generator[Tuple[int, int], None, None]:
        """
        处理音频数据，生成语音段
        
        Args:
            audio_data: 音频数据 (numpy array, int16)
            
        Yields:
            (start_frame, end_frame): 语音段的起始和结束帧索引
        """
        in_speech = False
        speech_start = 0
        silence_counter = 0
        silence_threshold = 5  # 连续 5 帧静音判定为说话结束
        
        for i in range(0, len(audio_data), self.frame_size):
            frame = audio_data[i:i + self.frame_size]
            
            if len(frame) < self.frame_size:
                break
            
            frame_bytes = frame.tobytes()
            is_speech = self.is_speech(frame_bytes)
            
            if is_speech:
                if not in_speech:
                    speech_start = i
                    in_speech = True
                silence_counter = 0
            else:
                if in_speech:
                    silence_counter += 1
                    if silence_counter >= silence_threshold:
                        yield (speech_start, i)
                        in_speech = False
                        silence_counter = 0
        
        # 处理末尾
        if in_speech:
            yield (speech_start, len(audio_data))
    
    def reset(self):
        """重置 VAD 状态"""
        self.window.clear()
        logger.debug("AcousticVAD reset")
