#!/usr/bin/env python3
"""
测试音频直接输入（无需 ASR）
"""
import asyncio
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import VoiceAgent
from loguru import logger

logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:HH:mm:ss} | {message}")


async def main():
    logger.info("🧪 测试音频直接输入...")
    
    agent = VoiceAgent(
        system_prompt="你是悠悠，一个又霸气又酷的女孩子。"
    )
    
    # 生成测试音频（模拟说话）
    sample_rate = 16000
    duration = 2  # 2 秒
    
    # 生成简单的正弦波（模拟语音）
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 440  # A4 音
    audio_data = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
    
    logger.info(f"生成测试音频：{len(audio_data)} samples, {duration}秒")
    
    # 处理音频
    logger.info("\n🎤 发送音频给 LLM...")
    
    async for event_type, data in agent.process_audio(audio_data):
        if event_type == "thinking":
            logger.info(f"状态：{data}")
        elif event_type == "text":
            print(data, end="", flush=True)
        elif event_type == "speaking":
            logger.info(f"\n状态：{data}")
        elif event_type == "audio":
            pass  # 音频数据
    
    logger.info("\n\n✅ 测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
