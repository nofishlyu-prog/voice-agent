"""
ASR 模块 - 阿里云智能语音识别
"""
import asyncio
import io
import wave
from typing import Optional
from loguru import logger
import dashscope
from dashscope.audio import asr


class DashScopeASR:
    """阿里云 DashScope 语音识别"""
    
    def __init__(self, api_key: str, model: str = "paraformer-realtime-v2"):
        self.api_key = api_key
        self.model = model
        dashscope.api_key = api_key
        logger.info(f"DashScopeASR initialized: model={model}")
    
    def _audio_to_wav(self, audio_data: bytes, sample_rate: int = 16000) -> bytes:
        """PCM 转 WAV"""
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    async def transcribe(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """
        语音识别
        
        Args:
            audio_data: PCM 音频
            sample_rate: 采样率
            
        Returns:
            识别文本
        """
        try:
            logger.debug(f"ASR transcribing: {len(audio_data)} bytes")
            
            # 转 WAV
            wav_data = self._audio_to_wav(audio_data, sample_rate)
            
            # 保存临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                f.write(wav_data)
                temp_path = f.name
            
            # 调用 ASR
            result = await asyncio.to_thread(
                self._call_asr,
                temp_path
            )
            
            # 清理
            import os
            os.unlink(temp_path)
            
            return result
            
        except Exception as e:
            logger.error(f"ASR error: {e}")
            return ""
    
    def _call_asr(self, file_path: str) -> str:
        """同步调用 ASR"""
        from dashscope.audio.asr import Recognition
        
        recognition = Recognition(
            model=self.model,
            format='wav',
            sample_rate=16000,
            disfluency_removal=False
        )
        
        result = recognition.call(file_path)
        
        if result.status_code == 200:
            if result.results and 'transcripts' in result.results:
                text = result.results['transcripts'][0]['text']
                logger.debug(f"ASR result: {text[:100]}...")
                return text
        
        logger.warning(f"ASR failed: {result.code}")
        return ""
