"""
LLM 模块 - 阿里云 Qwen 多模态模型
支持：文本 + 音频直接输入
"""
import asyncio
import base64
import io
import wave
from typing import Optional, List, Dict, AsyncGenerator
from loguru import logger
import dashscope
from dashscope import MultiModalConversation


class QwenOmniLLM:
    """Qwen 多模态 LLM (支持音频)"""
    
    def __init__(self, api_key: str, model: str = "qwen-vl-max"):
        self.api_key = api_key
        self.model = model
        dashscope.api_key = api_key
        
        self.messages: List[Dict] = []
        self.max_history = 6
        
        logger.info(f"QwenOmniLLM initialized: model={model}")
    
    def _audio_to_base64(self, audio_data: bytes, sample_rate: int = 16000) -> str:
        """PCM 转 WAV base64 (data URI 格式)"""
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)
        wav_buffer.seek(0)
        wav_b64 = base64.b64encode(wav_buffer.read()).decode('utf-8')
        # Qwen3-Omni-Flash 需要 data URI 格式
        return f"data:audio/wav;base64,{wav_b64}"
    
    def set_system_prompt(self, prompt: str):
        """设置系统提示"""
        self.messages.insert(0, {"role": "system", "content": [{"text": prompt}]})
        logger.info(f"System prompt set")
    
    async def chat(self, 
                   text: Optional[str] = None,
                   audio_data: Optional[bytes] = None,
                   sample_rate: int = 16000) -> AsyncGenerator[str, None]:
        """
        对话（支持文本或音频）
        
        Args:
            text: 文本输入
            audio_data: 音频数据 (PCM)
            sample_rate: 采样率
            
        Yields:
            LLM 回复
        """
        try:
            # 构建消息
            content = []
            
            if audio_data:
                audio_base64 = self._audio_to_base64(audio_data, sample_rate)
                content.append({"audio": audio_base64})
                logger.debug(f"Audio input: {len(audio_data)} bytes")
            
            if text:
                content.append({"text": text})
                logger.debug(f"Text input: {text[:50]}...")
            
            if not content:
                raise ValueError("需要 audio 或 text")
            
            # 添加用户消息
            self.messages.append({"role": "user", "content": content})
            
            # 调用多模态 API
            response = await asyncio.to_thread(
                MultiModalConversation.call,
                model=self.model,
                messages=self.messages
            )
            
            if response.status_code == 200 and response.output:
                full_response = self._parse_output(response.output)
                if full_response:
                    yield full_response
                    self._add_response(full_response)
                else:
                    yield "（思考中...）"
            else:
                error = f"API Error: {response.code if response else 'Unknown'}"
                logger.error(error)
                yield f"抱歉，出错了：{response.code if response else 'Unknown'}"
            
        except Exception as e:
            logger.error(f"LLM error: {e}")
            yield f"抱歉，出现了一些问题：{str(e)}"
    
    def _parse_output(self, output) -> str:
        """解析返回"""
        try:
            if hasattr(output, 'choices') and output.choices:
                content = output.choices[0].message.content
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    return ''.join(
                        item.get('text', '') if isinstance(item, dict) else str(item)
                        for item in content
                    )
            return ""
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return ""
    
    def _add_response(self, content: str):
        """保存回复"""
        self.messages.append({"role": "assistant", "content": [{"text": content}]})
        while len(self.messages) > self.max_history + 1:
            if self.messages[0].get("role") == "system":
                self.messages = [self.messages[0]] + self.messages[3:]
            else:
                self.messages = self.messages[2:]
    
    def clear_history(self):
        """清空历史"""
        system = next((m for m in self.messages if m.get("role") == "system"), None)
        self.messages = [system] if system else []
