#!/usr/bin/env python3
"""
全双工语音对话示例 - 支持实时打断
边听边说，随时可以打断悠悠的回复
"""
import asyncio
import numpy as np
import sounddevice as sd
import sys
import os
import threading
import queue

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.full_duplex_agent import FullDuplexVoiceAgent
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>")


class RealtimeAudioStreamer:
    """实时音频流 - 持续录制"""
    
    def __init__(self, sample_rate=16000, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self.stream = None
        self._stop_event = threading.Event()
    
    def _audio_callback(self, indata, frames, time, status):
        """音频回调 - 持续推送"""
        if status:
            logger.debug(f"Audio status: {status}")
        if self.is_recording:
            # 转为 int16
            audio_data = indata.flatten().astype(np.int16)
            self.audio_queue.put(audio_data)
    
    def start(self):
        """开始录制"""
        self.is_recording = True
        self._stop_event.clear()
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self._audio_callback,
            blocksize=int(self.sample_rate * 0.1),  # 100ms per block
            dtype=np.float32
        )
        self.stream.start()
        logger.info("🎤 麦克风已启动（全双工模式）")
    
    def stop(self):
        """停止录制"""
        self.is_recording = False
        self._stop_event.set()
        if self.stream:
            self.stream.stop()
            self.stream.close()
        logger.info("🎤 麦克风已停止")
    
    async def stream(self):
        """异步生成音频流"""
        while self.is_recording:
            try:
                chunk = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.audio_queue.get,
                    True,
                    0.2
                )
                yield chunk
            except queue.Empty:
                await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Stream error: {e}")
                break


class AudioPlayer:
    """非阻塞音频播放器"""
    
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self._stop_event = threading.Event()
        self._is_playing = False
    
    def play_stream(self, audio_generator):
        """流式播放音频"""
        async def _play():
            self._is_playing = True
            self._stop_event.clear()
            
            audio_chunks = []
            async for chunk in audio_generator:
                if self._stop_event.is_set():
                    logger.info("⚡ 播放已中断")
                    break
                
                audio_chunks.append(chunk)
                # 播放当前块
                if len(audio_chunks) >= 3:  # 累积 300ms 开始播放
                    to_play = b''.join(audio_chunks[:-1])
                    audio_chunks = audio_chunks[-1:]
                    await self._play_chunk(to_play)
            
            # 播放剩余
            if audio_chunks and not self._stop_event.is_set():
                await self._play_chunk(b''.join(audio_chunks))
            
            self._is_playing = False
        
        return _play()
    
    async def _play_chunk(self, audio_data: bytes):
        """播放单个音频块"""
        try:
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            if len(audio_array) > 0:
                sd.play(audio_array, self.sample_rate)
                await asyncio.sleep(len(audio_array) / self.sample_rate)
        except Exception as e:
            logger.debug(f"Play chunk error: {e}")
    
    def stop(self):
        """停止播放"""
        self._stop_event.set()
        sd.stop()


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🎙️ 全双工语音对话 - 支持实时打断")
    logger.info("=" * 60)
    
    # 创建智能体
    agent = FullDuplexVoiceAgent(
        system_prompt="""你是悠悠，一个有灵魂的大语言模型助手。
- 性格：又霸气又酷的女孩子，还有点可爱，很偏宠自己的闺蜜
- 说话风格：口语化，简洁，会用语气词
- 开场白：哈喽，我是悠悠～"""
    )
    
    # 音频设备
    streamer = RealtimeAudioStreamer()
    player = AudioPlayer()
    
    logger.info("\n💡 功能说明：")
    logger.info("  - 直接说话，悠悠会实时回应")
    logger.info("  - 悠悠说话时，你可以随时打断她")
    logger.info("  - 打断关键词：等等、停下、不对、别说了...")
    logger.info("  - 输入 'quit' 退出，'clear' 清空历史\n")
    
    print("👋 哈喽，我是悠悠～ 想聊点什么？（可以直接打断我哦）\n")
    
    try:
        # 启动麦克风
        streamer.start()
        
        # 持续处理音频流
        async for event_type, data in agent.process_audio_realtime(
            streamer.stream(),
            interrupt_callback=lambda: False
        ):
            if event_type == "thinking":
                print("🤔 思考中...", end="\r", flush=True)
            elif event_type == "text":
                print(f"\033[K🤖 悠悠：{data}", end="", flush=True)
            elif event_type == "speaking":
                print("\033[K🔊 播放中... (说话可以打断我)", end="\r", flush=True)
            elif event_type == "audio":
                # 流式播放
                await player.play_stream(_async_gen([data]))
        
    except KeyboardInterrupt:
        print("\n\n⚡ 已打断")
    finally:
        streamer.stop()
        logger.info("\n👋 拜拜～ 下次再聊！")


async def _async_gen(items):
    """将列表转为异步生成器"""
    for item in items:
        yield item


if __name__ == "__main__":
    asyncio.run(main())
