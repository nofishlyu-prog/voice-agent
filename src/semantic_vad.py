"""
语义 VAD (Semantic Voice Activity Detection)
基于规则判断用户是否说完话（turn detection）
快速、可靠，无需 API 调用
"""
from typing import Optional, List
from loguru import logger


class SemanticVAD:
    """语义语音活动检测 - 判断用户是否说完"""
    
    def __init__(self, api_key: str = "", threshold: float = 0.3):
        """
        初始化语义 VAD
        
        Args:
            api_key: 阿里云 DashScope API Key (保留参数，实际不使用)
            threshold: 结束判定阈值 (0-1) - 保留参数
        """
        self.api_key = api_key
        self.threshold = threshold
        
        # 对话历史用于上下文理解
        self.conversation_history = []
        
        logger.info(f"SemanticVAD initialized: rule-based (threshold={threshold})")
    
    async def is_turn_complete(self, text: str, context: Optional[List[dict]] = None) -> bool:
        """
        判断用户是否已经说完话
        
        Args:
            text: 当前识别的文本
            context: 对话上下文
            
        Returns:
            bool: 是否说完
        """
        # 使用基于规则的方法（快速、可靠）
        result = self.analyze_sentence_structure(text)
        logger.debug(f"SemanticVAD: '{text[:50]}...' -> {result}")
        return result
    
    def analyze_sentence_structure(self, text: str) -> bool:
        """
        基于规则的句子完整性分析
        
        Args:
            text: 文本
            
        Returns:
            bool: 是否完整
        """
        text = text.strip().lower()
        
        if not text:
            return False
        
        # 完整句子结束标志
        complete_endings = ['。', '！', '？', '!', '?', '了', '的', '吗', '呢', '吧', '啊', '哦']
        
        # 未完成标志 - 连接词开头
        incomplete_starters = [
            '因为', '所以', '但是', '如果', '虽然', '而且', '还有', '然后',
            '不过', '可是', '即使', '哪怕', '既然', '除非', '只要', '只有'
        ]
        
        # 未完成标志 - 结尾
        incomplete_endings = ['，', '、', '…', '...', '和', '与', '或', '等', '等等']
        
        # 明显未完成的短语
        incomplete_phrases = [
            '我想', '我要', '我觉得', '我认为', '我希望',
            '请问', '问一下', '能不能', '可不可以',
            '那个', '这个', '就是', '还有那个'
        ]
        
        # 检查是否包含未完成短语
        if any(text.endswith(p) for p in incomplete_phrases):
            logger.debug(f"  → Incomplete phrase detected")
            return False
        
        # 检查是否以连接词开头且没有完整结尾
        if any(text.startswith(s) for s in incomplete_starters):
            if not any(text.endswith(e) for e in complete_endings):
                logger.debug(f"  → Incomplete starter without ending")
                return False
        
        # 检查结尾是否有完整标志
        if any(text.endswith(e) for e in complete_endings):
            logger.debug(f"  → Complete ending detected")
            return True
        
        # 检查是否有未完成结尾
        if any(text.endswith(e) for e in incomplete_endings):
            logger.debug(f"  → Incomplete ending detected")
            return False
        
        # 短句（<8 字）默认完整
        if len(text) < 8:
            logger.debug(f"  → Short sentence (<8 chars), assuming complete")
            return True
        
        # 长句但没有结束标志，可能没说完
        if len(text) > 20:
            logger.debug(f"  → Long sentence (>20 chars) without ending, assuming incomplete")
            return False
        
        # 默认认为完整
        logger.debug(f"  → Default: complete")
        return True
    
    def reset(self):
        """重置对话历史"""
        self.conversation_history = []
        logger.debug("SemanticVAD history reset")
