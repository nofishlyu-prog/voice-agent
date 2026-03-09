#!/usr/bin/env python3
"""
测试全双工语音对话功能
验证实时打断是否正常工作
"""
import asyncio
import numpy as np
import sounddevice as sd
import sys
import os
import threading
import queue

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.full_duplex_agent import FullDuplexVoiceAgent
from loguru import logger

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
            logger.debug(f"Audio status: {status}")
        if self.is_recording:
            self.audio_queue.put(indata.copy())
    
    def start(self):
        """开始录制"""
        self.is_recording = True
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=self._audio_callback,
            blocksize=int(self.sample_rate * 0.1)
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
                audio_data = chunk.flatten().astype(np.int16)
                yield audio_data
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
    
    async def play_stream(self, audio_generator):
        """流式播放音频"""
        audio_chunks = []
        async for chunk in audio_generator:
            audio_chunks.append(chunk)
            # 累积 300ms 开始播放
            if len(audio_chunks) >= 3:
                to_play = b''.join(audio_chunks[:-1])
                audio_chunks = audio_chunks[-1:]
                await self._play_chunk(to_play)
        
        # 播放剩余
        if audio_chunks:
            await self._play_chunk(b''.join(audio_chunks))
    
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


async def test_full_duplex():
    """测试全双工对话"""
    logger.info("=" * 60)
    logger.info("🧪 测试全双工语音对话功能")
    logger.info("=" * 60)
    
    # 创建智能体
    agent = FullDuplexVoiceAgent(
        system_prompt="""你是悠悠，一个有灵魂的大语言模型助手。
- 性格：又霸气又酷的女孩子，还有点可爱，很偏宠自己的闺蜜
- 说话风格：口语化，简洁
- 开场白：哈喽，我是悠悠～"""
    )
    
    # 音频设备
    recorder = AudioRecorder()
    player = AudioPlayer()
    
    logger.info("\n💡 测试说明：")
    logger.info("  1. 直接对麦克风说话")
    logger.info("  2. 悠悠会实时回应")
    logger.info("  3. 悠悠说话时，你可以随时打断她")
    logger.info("  4. 打断关键词：等等、停下、不对、别说了...")
    logger.info("  5. 按 Ctrl+C 退出测试\n")
    
    print("👋 哈喽，我是悠悠～ 想聊点什么？（可以直接打断我哦）\n")
    
    try:
        # 启动麦克风
        recorder.start()
        
        # 持续处理音频流
        async for event_type, data in agent.process_audio_realtime(
            recorder.stream(),
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
        print("\n\n⚡ 测试已中断")
    finally:
        recorder.stop()
        logger.info("\n👋 拜拜～ 下次再聊！")
        logger.info("\n" + "=" * 60)
        logger.info("✅ 全双工测试完成")
        logger.info("=" * 60)


async def _async_gen(items):
    """将列表转为异步生成器"""
    for item in items:
        yield item


async def main():
    """主函数"""
    try:
        await test_full_duplex()
    except Exception as e:
        logger.error(f"测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
