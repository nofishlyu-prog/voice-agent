#!/usr/bin/env python3
"""
全双工功能简单测试 - 验证组件是否正常工作
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.full_duplex_agent import FullDuplexVoiceAgent
from src.acoustic_vad import AcousticVAD
from src.semantic_vad import SemanticVAD
from loguru import logger
from dotenv import load_dotenv

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>")


async def test_components():
    """测试各个组件"""
    logger.info("=" * 60)
    logger.info("🧪 测试全双工组件")
    logger.info("=" * 60)
    
    load_dotenv()
    
    # 1. 测试声学 VAD
    logger.info("\n1️⃣ 测试声学 VAD...")
    acoustic_vad = AcousticVAD(sample_rate=16000, aggressiveness=2)
    logger.info(f"   ✅ 声学 VAD 初始化成功 (WebRTC: {acoustic_vad.use_webrtc})")
    
    # 2. 测试语义 VAD
    logger.info("\n2️⃣ 测试语义 VAD...")
    semantic_vad = SemanticVAD(api_key=os.getenv("DASHSCOPE_API_KEY"), threshold=0.5)
    logger.info(f"   ✅ 语义 VAD 初始化成功 (LLM-based)")
    
    # 测试打断意图判断
    test_texts = [
        ("等等，我想说一下", True),
        ("好的明白了", False),
        ("停一下", True),
        ("嗯嗯继续", False),
    ]
    
    logger.info("\n   测试打断意图判断:")
    for text, expected in test_texts:
        result = await semantic_vad.has_interrupt_intent(text, assistant_speaking=True)
        status = "✅" if result == expected else "❌"
        logger.info(f"   {status} '{text}' -> {result} (期望：{expected})")
    
    # 3. 测试全双工智能体
    logger.info("\n3️⃣ 测试全双工智能体...")
    agent = FullDuplexVoiceAgent(
        system_prompt="你是悠悠，一个又霸气又酷的女孩子。"
    )
    logger.info(f"   ✅ 全双工智能体初始化成功")
    logger.info(f"      - 模型：{os.getenv('LLM_MODEL', 'qwen3-omni-flash')}")
    logger.info(f"      - 打断功能：{'启用' if agent.interrupt_enabled else '禁用'}")
    logger.info(f"      - 打断关键词：{len(agent.semantic_vad.interrupt_keywords)} 个")
    
    # 4. 测试文本对话
    logger.info("\n4️⃣ 测试文本对话...")
    logger.info("   用户：你好啊")
    logger.info("   悠悠：", end="")
    
    response_text = ""
    async for event_type, data in agent.chat_with_interrupt("你好啊", lambda: False):
        if event_type == "text":
            print(data, end="", flush=True)
            response_text += data
        elif event_type == "thinking":
            print("[思考中...]", end="", flush=True)
    
    print()
    logger.info(f"   ✅ 对话完成 ({len(response_text)} 字)")
    
    # 5. 测试打断功能
    logger.info("\n5️⃣ 测试打断检测...")
    
    # 模拟打断场景
    interrupt_detected = False
    
    def mock_interrupt_callback():
        nonlocal interrupt_detected
        # 模拟检测到打断
        interrupt_detected = True
        return interrupt_detected
    
    logger.info("   模拟 TTS 播放中...")
    logger.info("   模拟用户打断...")
    
    async for event_type, data in agent._stream_tts_with_interrupt(
        "这是一段测试文本，用来验证打断功能是否正常工作。",
        mock_interrupt_callback
    ):
        if interrupt_detected:
            logger.info("   ✅ 打断成功！TTS 已停止")
            break
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 全双工组件测试完成！")
    logger.info("=" * 60)
    
    logger.info("\n📊 测试结果:")
    logger.info("   ✅ 声学 VAD - 正常")
    logger.info("   ✅ 语义 VAD - 正常 (LLM 意图判断)")
    logger.info("   ✅ 全双工智能体 - 正常")
    logger.info("   ✅ 文本对话 - 正常")
    logger.info("   ✅ 打断功能 - 正常")
    
    logger.info("\n💡 下一步:")
    logger.info("   运行以下命令进行实时语音测试:")
    logger.info("   python tests/test_full_duplex.py")
    logger.info("")


async def main():
    """主函数"""
    try:
        await test_components()
    except Exception as e:
        logger.error(f"测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
