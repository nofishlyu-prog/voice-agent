"""
语义 VAD (Semantic Voice Activity Detection)
基于 LLM 判断用户是否说完话（turn detection）
"""
import asyncio
from typing import Optional, List
from loguru import logger
import dashscope
from dashscope import MultiModalConversation
import os


class SemanticVAD:
    """语义语音活动检测 - 判断用户是否说完"""
    
    def __init__(self, api_key: str, threshold: float = 0.3):
        """
        初始化语义 VAD
        
        Args:
            api_key: 阿里云 DashScope API Key
            threshold: 结束判定阈值 (0-1)
        """
        self.api_key = api_key
        self.threshold = threshold
        dashscope.api_key = api_key
        
        # 对话历史用于上下文理解
        self.conversation_history = []
        
        logger.info(f"SemanticVAD initialized: threshold={threshold}")
    
    async def is_turn_complete(self, text: str, context: Optional[List[dict]] = None) -> bool:
        """
        判断用户是否说完话
        
        Args:
            text: 当前识别的文本
            context: 对话上下文
            
        Returns:
            bool: 是否说完
        """
        try:
            # 构建判断 prompt
            prompt = f"""判断用户是否已经说完话。如果句子完整、意思表达清楚，返回 true；如果明显没说完、有停顿或等待继续，返回 false。
只返回 true 或 false，不要其他内容。

用户输入：{text}
"""
            
            messages = [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ]
            
            response = await asyncio.to_thread(
                MultiModalConversation.call,
                model="qwen-plus",
                messages=messages
            )
            
            if response.status_code == 200:
                result = response.output.choices[0].message.content.strip().lower()
                is_complete = "true" in result
                logger.debug(f"SemanticVAD result: {text[:50]}... -> {is_complete}")
                return is_complete
            else:
                logger.warning(f"SemanticVAD API error: {response.code}")
                # API 错误时默认认为说完
                return True
                
        except Exception as e:
            logger.error(f"SemanticVAD error: {e}")
            # 出错时默认认为说完
            return True
    
    def analyze_sentence_structure(self, text: str) -> bool:
        """
        基于规则的句子完整性分析（备用方案）
        
        Args:
            text: 文本
            
        Returns:
            bool: 是否完整
        """
        # 去除空白
        text = text.strip()
        
        if not text:
            return False
        
        # 完整句子标志
        complete_endings = ['。', '！', '？', '!', '?', '了', '的', '吗', '呢', '吧']
        
        # 未完成标志
        incomplete_starters = ['因为', '所以', '但是', '如果', '虽然', '而且', '还有', '然后']
        incomplete_endings = ['，', '、', '…', '...', '和', '与', '或']
        
        # 检查结尾
        if any(text.endswith(e) for e in complete_endings):
            return True
        
        # 检查是否以连接词开头但没结束
        if any(text.startswith(s) for s in incomplete_starters):
            if any(text.endswith(e) for e in incomplete_endings):
                return False
        
        # 短句默认完整
        if len(text) < 10:
            return True
        
        return True
    
    def reset(self):
        """重置对话历史"""
        self.conversation_history = []
        logger.debug("SemanticVAD history reset")
