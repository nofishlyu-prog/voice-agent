#!/usr/bin/env python3
"""
测试语义 VAD 的打断意图判断
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
    """测试打断意图判断"""
    load_dotenv()
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    logger.info("🧪 测试语义 VAD - 打断意图判断")
    logger.info("=" * 60)
    
    semantic_vad = SemanticVAD(api_key=api_key, threshold=0.5)
    
    # 测试用例：(文本，期望结果：True=有打断意图，False=无打断意图)
    test_cases = [
        # 明显的打断意图
        ("等等，我想说一下", True),
        ("停一下，你说的不对", True),
        ("别说了，听我说", True),
        ("不对，不是这样的", True),
        ("等一下，我还没说完", True),
        ("停，我不要听这个", True),
        ("错了错了", True),
        ("重新说", True),
        
        # 正常的对话回应（无打断意图）
        ("好的，我明白了", False),
        ("嗯嗯，继续说", False),
        ("然后呢", False),
        ("真的吗", False),
        ("太有意思了", False),
        ("我也觉得", False),
        ("对对对", False),
        
        # 边界情况
        ("我想问一下", False),  # 询问，不是打断
        ("那个", False),  # 犹豫，不是打断
        ("喂", False),  # 招呼，不是打断
    ]
    
    passed = 0
    failed = 0
    
    for text, expected in test_cases:
        # 模拟 AI 正在说话的场景
        result = await semantic_vad.has_interrupt_intent(
            text=text,
            assistant_speaking=True
        )
        
        status = "✅" if result == expected else "❌"
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        logger.info(f"{status} '{text}'")
        logger.info(f"   判断：{result}, 期望：{expected}")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"测试结果：{passed} 通过，{failed} 失败")
    logger.info(f"准确率：{passed/(passed+failed)*100:.1f}%")
    
    if passed / (passed + failed) >= 0.8:
        logger.info("✅ 打断意图判断功能正常！")
    else:
        logger.error("❌ 准确率不足 80%，需要优化")


if __name__ == "__main__":
    asyncio.run(main())
