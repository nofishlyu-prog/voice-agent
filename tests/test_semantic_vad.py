#!/usr/bin/env python3
"""
测试语义 VAD - 判断用户是否说完话
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.semantic_vad import SemanticVAD
from loguru import logger
from dotenv import load_dotenv

# 配置日志
logger.remove()
logger.add(sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>")


async def main():
    """测试语义 VAD"""
    load_dotenv()
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    logger.info("🧪 测试语义 VAD")
    logger.info("=" * 60)
    
    semantic_vad = SemanticVAD(api_key=api_key, threshold=0.3)
    
    # 测试用例
    test_cases = [
        # (文本，期望结果：True=说完，False=没说完)
        ("你好", True),
        ("今天天气怎么样", True),
        ("我想问一下", False),
        ("因为今天下雨", False),
        ("所以我不出去了", True),
        ("但是", False),
        ("然后", False),
        ("给我讲个笑话吧", True),
        ("如果明天", False),
        ("虽然我很想去", False),
        ("拜拜", True),
        ("等等，我还没说完", False),
        ("停一下", True),
    ]
    
    passed = 0
    failed = 0
    
    for text, expected in test_cases:
        result = await semantic_vad.is_turn_complete(text)
        
        # 也测试基于规则的方法
        rule_result = semantic_vad.analyze_sentence_structure(text)
        
        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        logger.info(f"{status} '{text}'")
        logger.info(f"   LLM 判断：{result}, 规则判断：{rule_result}, 期望：{expected}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"测试结果：{passed} 通过，{failed} 失败")
    logger.info(f"准确率：{passed/(passed+failed)*100:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
