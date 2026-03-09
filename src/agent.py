"""
Voice Agent - 语音对话智能体
架构：声学 VAD → Qwen 多模态 LLM → TTS
无需 ASR，LLM 直接理解音频
"""
import asyncio
import numpy as np
from typing import Optional, AsyncGenerator
from loguru import logger
from dotenv import load_dotenv
import os

from .acoustic_vad import AcousticVAD
from .llm import QwenOmniLLM
from .tts import DashScopeTTS


class VoiceAgent:
    """语音对话智能体"""
    
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
        
        # 多模态 LLM (直接处理音频)
        self.llm = QwenOmniLLM(
            api_key=self.api_key,
            model=os.getenv("LLM_MODEL", "qwen-omni-turbo")
        )
        
        # TTS
        self.tts = DashScopeTTS(
            api_key=self.api_key,
            model=os.getenv("TTS_MODEL", "sambert-zhichu-v1"),
            voice=os.getenv("TTS_VOICE", "zhichu")
        )
        
        if system_prompt:
            self.llm.set_system_prompt(system_prompt)
        
        logger.info(f"VoiceAgent initialized: model={os.getenv('LLM_MODEL', 'qwen-omni-turbo')}")
    
    async def chat(self, text: str) -> AsyncGenerator[tuple, None]:
        """文本对话"""
        logger.info(f"User: {text}")
        yield ("thinking", None)
        
        full_response = ""
        async for text_chunk in self.llm.chat(text=text):
            full_response += text_chunk
            yield ("text", text_chunk)
        
        logger.info(f"Assistant: {full_response}")
        
        yield ("speaking", None)
        async for audio_chunk in self.tts.synthesize(full_response):
            yield ("audio", audio_chunk)
    
    async def process_audio(self, 
                           audio_data: np.ndarray) -> AsyncGenerator[tuple, None]:
        """
        处理音频 - LLM 直接理解
        流程：VAD → LLM (多模态) → TTS
        """
        logger.info(f"Processing audio: {len(audio_data)} samples")
        
        # 1. VAD 检测语音段
        speech_segments = list(self.acoustic_vad.process_audio(audio_data))
        
        if not speech_segments:
            logger.debug("No speech detected")
            yield ("listening", None)
            return
        
        # 2. 处理第一个语音段
        start, end = speech_segments[0]
        segment = audio_data[start:end]
        segment_bytes = segment.tobytes()
        
        logger.info(f"Speech segment: {len(segment_bytes)} bytes")
        
        # 3. 多模态 LLM 处理（直接理解音频）
        yield ("thinking", "🎤 思考中...")
        
        full_response = ""
        async for text_chunk in self.llm.chat(audio_data=segment_bytes, sample_rate=self.sample_rate):
            full_response += text_chunk
            yield ("text", text_chunk)
        
        logger.info(f"Assistant: {full_response}")
        
        # 4. TTS 输出
        yield ("speaking", "🔊 播放中...")
        async for audio_chunk in self.tts.synthesize(full_response):
            yield ("audio", audio_chunk)
        
        self.acoustic_vad.reset()
    
    def clear_history(self):
        """清空历史"""
        self.llm.clear_history()
    
    def set_system_prompt(self, prompt: str):
        """设置系统提示"""
        self.llm.set_system_prompt(prompt)
