#!/usr/bin/env python3
"""
快速聊天测试 - 预定义对话
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import VoiceAgent
from loguru import logger
from dotenv import load_dotenv

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>")


async def main():
    """测试对话"""
    load_dotenv()
    
    # 创建智能体
    agent = VoiceAgent(
        system_prompt="""你是悠悠，一个有灵魂的大语言模型助手。
- 性格：又霸气又酷的女孩子，还有点可爱，很偏宠自己的闺蜜
- 说话风格：口语化，简洁，会用语气词
- 开场白：哈喽，我是悠悠～"""
    )
    
    logger.info("🎙️ 悠悠已上线！\n")
    
    # 预定义的对话
    test_conversation = [
        "你好啊",
        "今天心情怎么样？",
        "给我讲个笑话",
        "拜拜",
    ]
    
    for user_input in test_conversation:
        logger.info(f"\n👤 你：{user_input}")
        logger.info("🤖 悠悠：", end="")
        
        full_response = ""
        async for event_type, data in agent.chat(user_input):
            if event_type == "text":
                print(data, end="", flush=True)
                full_response += data
            elif event_type == "thinking":
                print("[思考中...]", end="", flush=True)
        
        print()
        logger.info(f"✅ ({len(full_response)} 字)\n")
        await asyncio.sleep(0.5)
    
    logger.info("\n💬 测试完成！")
    logger.info("\n💡 提示：要实时聊天，请运行:")
    logger.info("   cd ~/.openclaw/workspace/voice-agent")
    logger.info("   source .venv/bin/activate")
    logger.info("   python examples/chat_demo.py")


if __name__ == "__main__":
    asyncio.run(main())
