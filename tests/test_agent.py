#!/usr/bin/env python3
"""
测试 Voice Agent
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent import VoiceAgent
from loguru import logger

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>")


async def main():
    """测试智能体"""
    logger.info("🧪 开始测试 Voice Agent (qwen3-omni-flash)...")
    
    agent = VoiceAgent(
        system_prompt="你是悠悠，一个又霸气又酷的女孩子，说话简洁有趣。"
    )
    
    logger.info("✅ 智能体创建成功")
    
    test_messages = [
        "你好，介绍一下自己",
        "今天天气怎么样",
    ]
    
    for msg in test_messages:
        logger.info(f"\n📝 用户：{msg}")
        logger.info("🤖 悠悠：", end="")
        
        full_response = ""
        async for event_type, data in agent.chat(msg):
            if event_type == "text":
                print(data, end="", flush=True)
                full_response += data
            elif event_type == "thinking":
                print("[思考]", end="", flush=True)
            elif event_type == "speaking":
                print("[TTS]", end="", flush=True)
        
        print()
        logger.info(f"✅ 回复完成 ({len(full_response)} 字)")
    
    logger.info("\n🎉 测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
