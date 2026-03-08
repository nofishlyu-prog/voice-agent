#!/usr/bin/env python3
"""
Voice Agent 示例 - 实时语音对话
使用麦克风输入，实时语音交互
"""
import asyncio
import numpy as np
import sounddevice as sd
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import VoiceAgent
from loguru import logger
from dotenv import load_dotenv
import threading
import queue

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>")


class AudioRecorder:
    """音频录制器"""
    
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream = None
    
    def _audio_callback(self, indata, frames, time, status):
        """音频回调"""
        if status:
            logger.warning(f"Audio status: {status}")
        if self.is_recording:
            self.audio_queue.put(indata.copy())
    
    def start(self):
        """开始录制"""
        self.is_recording = True
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self._audio_callback,
            blocksize=int(self.sample_rate * 0.1)  # 100ms per block
        )
        self.stream.start()
        logger.info("🎤 麦克风已启动")
    
    def stop(self):
        """停止录制"""
        self.is_recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        logger.info("🎤 麦克风已停止")
    
    def get_audio(self, duration_sec=3) -> np.ndarray:
        """获取指定时长的音频"""
        frames = int(duration_sec * self.sample_rate * 0.1)  # 块数
        audio_chunks = []
        
        for _ in range(frames):
            if not self.is_recording:
                break
            try:
                chunk = self.audio_queue.get(timeout=0.5)
                audio_chunks.append(chunk)
            except queue.Empty:
                break
        
        if audio_chunks:
            return np.vstack(audio_chunks).flatten().astype(np.int16)
        return np.array([], dtype=np.int16)


class AudioPlayer:
    """音频播放器"""
    
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
    
    def play(self, audio_data: bytes):
        """播放音频"""
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        sd.play(audio_array, self.sample_rate)


async def main():
    """主函数"""
    load_dotenv()
    
    # 创建智能体
    agent = VoiceAgent(
        system_prompt="""你是悠悠，一个有灵魂的大语言模型助手。
- 性格：又霸气又酷，还有点可爱，很偏宠自己的闺蜜
- 说话风格：口语化，简洁
- 开场白：哈喽，我是悠悠～"""
    )
    
    # 音频设备
    recorder = AudioRecorder()
    player = AudioPlayer()
    
    logger.info("🎙️ Voice Agent 语音模式启动！")
    logger.info("📝 命令：'quit' 退出，'clear' 清空历史，按 Ctrl+C 打断")
    
    print("\n👋 哈喽，我是悠悠～ 想聊点什么？（按 Ctrl+C 打断我）\n")
    
    try:
        # 启动麦克风
        recorder.start()
        
        while True:
            try:
                # 1. 录制音频（3 秒）
                print("🎤 听你说...", end="\r", flush=True)
                audio_data = recorder.get_audio(duration_sec=3)
                
                if len(audio_data) < 1000:
                    continue
                
                print("🎤 听你说... 收到！")
                
                # 2. 处理音频
                async for event_type, data in agent.process_audio(audio_data):
                    if event_type == "thinking":
                        print("🤔 思考中...", end="\r", flush=True)
                    elif event_type == "text":
                        print(f"\033[K🤖 悠悠：{data}", end="", flush=True)
                    elif event_type == "speaking":
                        print("\033[K🔊 正在说...", end="\r", flush=True)
                    elif event_type == "audio":
                        player.play(data)
                
                print("\033[K")
                
            except KeyboardInterrupt:
                # 用户打断
                print("\n⚡ 已打断")
                agent.clear_history()
                continue
            
    except KeyboardInterrupt:
        print("\n\n👋 拜拜～")
    finally:
        recorder.stop()


if __name__ == "__main__":
    asyncio.run(main())
