"""
全双工语音对话智能体
支持实时打断、边听边说
架构：声学 VAD + 语义 VAD（LLM 判断打断意图）→ LLM → TTS (流式播放)
"""
import asyncio
import numpy as np
from typing import Optional, AsyncGenerator, List, Callable
from loguru import logger
from dotenv import load_dotenv
import os
import threading
import queue
from collections import deque

from .acoustic_vad import AcousticVAD
from .semantic_vad import SemanticVAD
from .llm import QwenOmniLLM
from .tts import DashScopeTTS


class AudioBuffer:
    """音频缓冲区 - 线程安全"""
    
    def __init__(self, max_seconds=10, sample_rate=16000):
        self.sample_rate = sample_rate
        self.max_samples = max_seconds * sample_rate
        self.buffer = deque()
        self.lock = threading.Lock()
    
    def add(self, audio_data: np.ndarray):
        """添加音频数据"""
        with self.lock:
            self.buffer.extend(audio_data)
            while len(self.buffer) > self.max_samples:
                self.buffer.popleft()
    
    def get_all(self) -> np.ndarray:
        """获取所有数据并清空"""
        with self.lock:
            data = np.array(list(self.buffer), dtype=np.int16)
            self.buffer.clear()
            return data
    
    def clear(self):
        """清空缓冲区"""
        with self.lock:
            self.buffer.clear()
    
    def __len__(self):
        with self.lock:
            return len(self.buffer)


class FullDuplexVoiceAgent:
    """全双工语音对话智能体 - 支持基于意图的实时打断"""
    
    def __init__(self,
                 api_key: Optional[str] = None,
                 system_prompt: Optional[str] = None):
        load_dotenv()
        
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("需要设置 DASHSCOPE_API_KEY")
        
        self.sample_rate = int(os.getenv("SAMPLE_RATE", "16000"))
        
        # 初始化组件
        self.acoustic_vad = AcousticVAD(
            sample_rate=self.sample_rate,
            aggressiveness=int(os.getenv("VAD_AGGRESSIVENESS", "2"))
        )
        
        # 语义 VAD (LLM 判断打断意图)
        self.semantic_vad = SemanticVAD(
            api_key=self.api_key,
            threshold=float(os.getenv("SEMANTIC_VAD_THRESHOLD", "0.5"))
        )
        
        # LLM
        self.llm = QwenOmniLLM(
            api_key=self.api_key,
            model=os.getenv("LLM_MODEL", "qwen3-omni-flash")
        )
        
        # TTS
        self.tts = DashScopeTTS(
            api_key=self.api_key,
            model=os.getenv("TTS_MODEL", "sambert-zhichu-v1"),
            voice=os.getenv("TTS_VOICE", "zhichu")
        )
        
        if system_prompt:
            self.llm.set_system_prompt(system_prompt)
        
        # 状态管理
        self.is_speaking = False
        self.is_listening = False
        self.interrupt_enabled = True
        self.audio_buffer = AudioBuffer(sample_rate=self.sample_rate)
        self.current_response = ""
        
        logger.info(f"FullDuplexVoiceAgent initialized: model={os.getenv('LLM_MODEL', 'qwen3-omni-flash')}")
        logger.info(f"Interrupt detection: LLM-based intent judgment")
    
    def _check_interrupt(self, text: str) -> bool:
        """检查是否包含打断关键词（快速判断）"""
        text_lower = text.lower()
        for keyword in self.semantic_vad.interrupt_keywords:
            if keyword in text_lower:
                logger.info(f"Interrupt keyword detected: {keyword}")
                return True
        return False
    
    async def _stream_tts_with_interrupt(self, 
                                          text: str,
                                          interrupt_callback: Callable[[], bool]) -> AsyncGenerator[bytes, None]:
        """
        流式播放 TTS，支持中断检测
        
        Args:
            text: 要合成的文本
            interrupt_callback: 中断检测回调，返回 True 表示需要中断
            
        Yields:
            音频数据块
        """
        self.is_speaking = True
        self.current_response = text
        
        try:
            async for chunk in self.tts.synthesize(text):
                # 检查是否需要中断
                if self.interrupt_enabled and interrupt_callback():
                    logger.info("TTS interrupted by user")
                    self.is_speaking = False
                    return
                
                yield chunk
        finally:
            self.is_speaking = False
    
    async def chat_with_interrupt(self, 
                                   text: str,
                                   interrupt_callback: Callable[[], bool]) -> AsyncGenerator[tuple, None]:
        """
        文本对话，支持播放中断
        
        Args:
            text: 用户输入
            interrupt_callback: 中断检测回调
            
        Yields:
            (event_type, data)
        """
        logger.info(f"User: {text}")
        yield ("thinking", None)
        
        full_response = ""
        async for text_chunk in self.llm.chat(text=text):
            full_response += text_chunk
            yield ("text", text_chunk)
        
        logger.info(f"Assistant: {full_response}")
        
        # 流式播放，支持中断
        yield ("speaking", "🔊 播放中...")
        async for audio_chunk in self._stream_tts_with_interrupt(full_response, interrupt_callback):
            yield ("audio", audio_chunk)
    
    async def _detect_user_speech(self) -> Optional[str]:
        """
        检测用户语音并识别内容（用于打断检测）
        
        Returns:
            识别的文本，如果没有检测到语音则返回 None
        """
        # 检查缓冲区是否有足够的音频
        if len(self.audio_buffer) < self.sample_rate * 0.5:  # 至少 0.5 秒
            return None
        
        # 获取音频
        audio_data = self.audio_buffer.get_all()
        
        # 声学 VAD 检测是否有人声
        if len(audio_data) > 0:
            is_speech = self.acoustic_vad.is_speech(audio_data.tobytes())
            if not is_speech:
                return None
        
        # TODO: 这里需要集成 ASR 来识别语音内容
        # 目前简化处理：如果检测到语音，返回占位符
        if len(audio_data) > self.sample_rate * 0.5:
            logger.debug(f"User speech detected: {len(audio_data)} samples")
            return "[user_speech]"  # 占位符，表示检测到用户语音
        
        return None
    
    async def _check_interrupt_intent(self) -> bool:
        """
        检查用户是否有打断意图
        
        Returns:
            bool: 是否有打断意图
        """
        # 检测用户语音
        user_text = await self._detect_user_speech()
        
        if not user_text:
            return False
        
        # 使用语义 VAD 判断打断意图
        has_intent = await self.semantic_vad.has_interrupt_intent(
            text=user_text,
            assistant_speaking=self.is_speaking
        )
        
        if has_intent:
            logger.info(f"Interrupt intent detected: {user_text}")
        
        return has_intent
    
    async def process_audio_realtime(self,
                                      audio_stream: AsyncGenerator[np.ndarray, None],
                                      interrupt_callback: Optional[Callable[[], bool]] = None) -> AsyncGenerator[tuple, None]:
        """
        实时处理音频流 - 全双工模式
        
        Args:
            audio_stream: 音频流生成器
            interrupt_callback: 外部中断回调
            
        Yields:
            (event_type, data)
        """
        accumulated_audio = []
        silence_counter = 0
        silence_threshold = 10  # 连续 10 个静音帧判定为说话结束
        
        async for audio_chunk in audio_stream:
            # 添加到缓冲区
            self.audio_buffer.add(audio_chunk)
            
            # 声学 VAD 检测
            is_speech = self.acoustic_vad.is_speech(audio_chunk.tobytes())
            
            if is_speech:
                silence_counter = 0
                if not self.is_listening:
                    self.is_listening = True
                    logger.debug("Speech detected")
            else:
                silence_counter += 1
            
            # 检测到沉默，准备处理
            if silence_counter >= silence_threshold and len(self.audio_buffer) > 0:
                # 获取音频
                audio_data = self.audio_buffer.get_all()
                
                if len(audio_data) > 1000:  # 至少 1000 个采样点
                    logger.info(f"Processing speech segment: {len(audio_data)} samples")
                    
                    # 处理音频并获取回复
                    async for event_type, data in self._process_speech(audio_data):
                        if event_type == "text":
                            # 有文本回复时，启动打断检测
                            yield ("speaking", "🔊 播放中...")
                            async for audio_chunk in self._stream_tts_with_interrupt(
                                data,
                                lambda: self._check_user_interrupt() or (interrupt_callback and interrupt_callback())
                            ):
                                yield ("audio", audio_chunk)
                        else:
                            yield (event_type, data)
                
                silence_counter = 0
                self.is_listening = False
                self.acoustic_vad.reset()
        
        # 处理剩余音频
        if len(self.audio_buffer) > 0:
            audio_data = self.audio_buffer.get_all()
            if len(audio_data) > 1000:
                async for event_type, data in self._process_speech(audio_data):
                    yield (event_type, data)
    
    def _check_user_interrupt(self) -> bool:
        """检查用户是否有打断行为（用于 TTS 播放时的打断）"""
        # 检查缓冲区是否有新的语音输入
        if len(self.audio_buffer) > self.sample_rate * 0.5:  # 超过 0.5 秒
            audio_data = self.audio_buffer.get_all()
            # 简单能量检测
            energy = np.sum(np.abs(audio_data.astype(float)))
            if energy > len(audio_data) * 500:  # 能量阈值
                logger.info("User speech detected during TTS")
                # TODO: 这里可以调用语义 VAD 判断是否有打断意图
                # 目前简化处理：检测到语音就认为想打断
                return True
        return False
    
    async def _process_speech(self, audio_data: np.ndarray) -> AsyncGenerator[tuple, None]:
        """
        处理语音段
        
        Args:
            audio_data: 语音数据
            
        Yields:
            (event_type, data)
        """
        yield ("thinking", "🎤 思考中...")
        
        # LLM 处理音频
        audio_bytes = audio_data.tobytes()
        full_response = ""
        
        async for text_chunk in self.llm.chat(audio_data=audio_bytes, sample_rate=self.sample_rate):
            full_response += text_chunk
            yield ("text", text_chunk)
        
        logger.info(f"Assistant: {full_response}")
        
        self.acoustic_vad.reset()
    
    def clear_history(self):
        """清空历史"""
        self.llm.clear_history()
        self.semantic_vad.reset()
    
    def set_system_prompt(self, prompt: str):
        """设置系统提示"""
        self.llm.set_system_prompt(prompt)
    
    def enable_interrupt(self, enabled: bool = True):
        """启用/禁用打断功能"""
        self.interrupt_enabled = enabled
        logger.info(f"Interrupt {'enabled' if enabled else 'disabled'}")
