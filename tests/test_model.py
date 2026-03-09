#!/usr/bin/env python3
"""
测试 Qwen3-Omni-Flash 模型调用
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm import QwenOmniLLM
from loguru import logger
from dotenv import load_dotenv

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>")


async def test_text_chat():
    """测试文本对话"""
    load_dotenv()
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    model = os.getenv("LLM_MODEL", "qwen3-omni-flash")
    
    logger.info(f"🧪 测试模型：{model}")
    logger.info(f"API Key: {api_key[:10]}...")
    
    llm = QwenOmniLLM(api_key=api_key, model=model)
    
    test_messages = [
        "你好，介绍一下自己",
        "今天天气怎么样？",
    ]
    
    for msg in test_messages:
        logger.info(f"\n📝 用户：{msg}")
        logger.info("🤖 AI：", end="")
        
        full_response = ""
        try:
            async for chunk in llm.chat(text=msg):
                print(chunk, end="", flush=True)
                full_response += chunk
            
            print()
            if full_response:
                logger.info(f"✅ 回复成功 ({len(full_response)} 字)")
            else:
                logger.warning("⚠️ 回复为空")
        except Exception as e:
            logger.error(f"❌ 调用失败：{e}")
            return False
    
    return True


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("Qwen3-Omni-Flash 模型测试")
    logger.info("=" * 50)
    
    success = await test_text_chat()
    
    logger.info("\n" + "=" * 50)
    if success:
        logger.info("✅ 测试通过！模型可以正常调用")
    else:
        logger.error("❌ 测试失败！请检查模型名称或 API Key")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
