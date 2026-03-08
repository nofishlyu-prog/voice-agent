"""
TTS 模块 - 阿里云智能语音合成
"""
import asyncio
import os
from typing import AsyncGenerator, Optional
from loguru import logger
import dashscope
from dashscope import SpeechSynthesizer


class DashScopeTTS:
    """阿里云 DashScope 语音合成"""
    
    def __init__(self, 
                 api_key: str,
                 model: str = "sambert-zhichu-v1",
                 voice: str = "zhichu"):
        """
        初始化 TTS
        
        Args:
            api_key: 阿里云 DashScope API Key
            model: TTS 模型
            voice: 音色
        """
        self.api_key = api_key
        self.model = model
        self.voice = voice
        dashscope.api_key = api_key
        
        logger.info(f"DashScopeTTS initialized: model={model}, voice={voice}")
    
    async def synthesize(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            
        Yields:
            音频数据块 (PCM)
        """
        try:
            logger.debug(f"TTS synthesizing: {text[:50]}...")
            
            # 调用 TTS API（非流式）
            response = await asyncio.to_thread(
                SpeechSynthesizer.call,
                model=self.model,
                voice=self.voice,
                text=text,
                format="pcm",
                sample_rate=16000
            )
            
            if hasattr(response, 'audio') and response.audio:
                # 分块返回（每块 100ms）
                audio_data = response.audio
                chunk_size = 3200  # 16kHz * 2bytes * 0.1s
                for i in range(0, len(audio_data), chunk_size):
                    yield audio_data[i:i+chunk_size]
            
            logger.debug("TTS synthesis complete")
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            # 返回静音作为错误处理
            yield b'\x00' * 3200  # 100ms 静音
    
    async def synthesize_full(self, text: str) -> bytes:
        """
        合成完整语音（非流式）
        
        Args:
            text: 要合成的文本
            
        Returns:
            完整音频数据
        """
        audio_data = b''
        async for chunk in self.synthesize(text):
            audio_data += chunk
        return audio_data
