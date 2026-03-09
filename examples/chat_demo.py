#!/usr/bin/env python3
"""
Voice Agent 示例 - 文本对话模式（优化版）
快速响应 + 流式输出
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
    """主函数"""
    load_dotenv()
    
    # 创建智能体（优化人设）
    agent = VoiceAgent(
        system_prompt="""你是悠悠，一个有灵魂的大语言模型助手。
性格：又霸气又酷的女孩子，还有点可爱，很偏宠自己的闺蜜
说话风格：
- 口语化、简洁，不要用书面语
- 会用语气词如"啊、呢、啦、嘛"
- 回复简短有趣，不要啰嗦
- 像朋友聊天一样自然
不要：
- 不要说"还有什么可以帮你"
- 不要尝试结束对话
- 不要用 markdown 或列表
开场白：哈喽，我是悠悠～"""
    )
    
    logger.info("🎙️ Voice Agent 启动！(qwen3-omni-flash)")
    print("\n👋 哈喽，我是悠悠～ 今天想聊点什么？\n")
    print("💡 输入 'quit' 退出，'clear' 清空历史\n")
    
    while True:
        try:
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, input, "你： "
            )
            
            user_input = user_input.strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', '退出']:
                print("\n👋 拜拜～ 下次再聊！")
                break
            
            if user_input.lower() in ['clear', '清空']:
                agent.clear_history()
                print("✅ 对话历史已清空\n")
                continue
            
            # 处理对话
            first_chunk = True
            async for event_type, data in agent.chat(user_input):
                if event_type == "thinking":
                    print("\n🤖 悠悠：", end="", flush=True)
                elif event_type == "text":
                    if first_chunk:
                        first_chunk = False
                    print(data, end="", flush=True)
                elif event_type == "speaking":
                    pass
                elif event_type == "audio":
                    pass
            
            print("\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 拜拜～")
            break
        except Exception as e:
            logger.error(f"错误：{e}")
            print(f"\n❌ 出错：{e}\n")


if __name__ == "__main__":
    asyncio.run(main())
