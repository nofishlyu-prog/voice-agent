"""
语义 VAD (Semantic Voice Activity Detection)
基于 LLM 判断用户是否有打断意图
"""
import asyncio
from typing import Optional, List
from loguru import logger
import dashscope
from dashscope import MultiModalConversation


class SemanticVAD:
    """语义语音活动检测 - 判断用户是否有打断意图"""
    
    def __init__(self, api_key: str, threshold: float = 0.5):
        """
        初始化语义 VAD
        
        Args:
            api_key: 阿里云 DashScope API Key
            threshold: 打断判定阈值 (0-1)，越低越容易判定为打断
        """
        self.api_key = api_key
        self.threshold = threshold
        dashscope.api_key = api_key
        
        # 对话历史用于上下文理解
        self.conversation_history = []
        
        # 打断意图关键词（用于辅助判断）
        self.interrupt_keywords = [
            "等等", "等一下", "停下", "停一下", "停",
            "不要说了", "别说", "别说了",
            "不对", "错了", "不是这样", "不是",
            "取消", "停止", "闭嘴", "打断", "慢点", "重新说",
            "喂", "哎", "那个", "我问", "我想说"
        ]
        
        logger.info(f"SemanticVAD initialized: LLM-based (threshold={threshold})")
    
    async def has_interrupt_intent(self, 
                                    text: str, 
                                    assistant_speaking: bool = False,
                                    context: Optional[List[dict]] = None) -> bool:
        """
        判断用户是否有打断意图
        
        Args:
            text: 当前识别的文本（ASR 结果）
            assistant_speaking: AI 是否正在说话
            context: 对话上下文
            
        Returns:
            bool: 是否有打断意图
        """
        try:
            # 如果 AI 没有在说话，不需要判断打断
            if not assistant_speaking:
                return False
            
            # 快速检查：包含打断关键词
            if self._contains_interrupt_keyword(text):
                logger.debug(f"Interrupt keyword detected: {text[:50]}...")
                return True
            
            # 使用 LLM 判断打断意图
            return await self._llm_judge_interrupt(text, context)
            
        except Exception as e:
            logger.error(f"SemanticVAD error: {e}")
            # 出错时使用关键词判断
            return self._contains_interrupt_keyword(text)
    
    def _contains_interrupt_keyword(self, text: str) -> bool:
        """快速检查是否包含打断关键词"""
        text_lower = text.lower()
        for keyword in self.interrupt_keywords:
            if keyword in text_lower:
                return True
        return False
    
    async def _llm_judge_interrupt(self, text: str, context: Optional[List[dict]] = None) -> bool:
        """
        使用 LLM 判断是否有打断意图
        
        Args:
            text: 用户输入的文本
            context: 对话上下文
            
        Returns:
            bool: 是否有打断意图
        """
        try:
            # 构建判断 prompt
            prompt = self._build_interrupt_prompt(text, context)
            
            messages = [
                {
                    "role": "system",
                    "content": [{"text": "你是一个对话意图判断助手，负责判断用户是否有打断 AI 说话的意图。"}]
                },
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ]
            
            # 调用模型
            response = await asyncio.to_thread(
                MultiModalConversation.call,
                model="qwen-turbo",
                messages=messages,
                max_tokens=10
            )
            
            if response.status_code == 200:
                result = response.output.choices[0].message.content.strip().lower()
                # 解析结果
                has_intent = self._parse_interrupt_result(result)
                logger.debug(f"LLM interrupt judge: '{text[:50]}...' -> {has_intent}")
                return has_intent
            else:
                logger.warning(f"SemanticVAD API error: {response.code}")
                # API 错误时退回关键词判断
                return self._contains_interrupt_keyword(text)
                
        except Exception as e:
            logger.error(f"LLM interrupt judge error: {e}")
            return self._contains_interrupt_keyword(text)
    
    def _build_interrupt_prompt(self, text: str, context: Optional[List[dict]] = None) -> str:
        """构建打断意图判断的 prompt"""
        
        context_info = ""
        if context and len(context) > 0:
            # 提取最近的对话历史
            recent = context[-2:] if len(context) >= 2 else context
            context_info = "\n对话历史:\n" + "\n".join(
                f"  {msg['role']}: {msg['content'][0].get('text', '')[:50]}" 
                for msg in recent
            )
        
        prompt = f"""请判断用户是否有打断 AI 说话的意图。

{context_info}

用户当前输入："{text}"

判断标准：
1. 如果用户想让 AI 停止说话，返回 true
2. 如果用户想纠正 AI 或表达不同意见，返回 true  
3. 如果用户想插话或转移话题，返回 true
4. 如果用户只是正常的对话回应，返回 false

只返回 true 或 false，不要其他内容。"""
        
        return prompt
    
    def _parse_interrupt_result(self, result: str) -> bool:
        """解析 LLM 返回的打断判断结果"""
        result = result.strip().lower()
        
        # 直接匹配
        if result in ['true', '是', 'yes', '有']:
            return True
        if result in ['false', '否', 'no', '没有']:
            return False
        
        # 包含判断
        if 'true' in result or '是' in result or '有' in result or '打断' in result:
            return True
        
        # 默认认为没有打断意图
        return False
    
    async def is_turn_complete(self, text: str, context: Optional[List[dict]] = None) -> bool:
        """
        判断用户是否已经说完话（用于 turn-taking）
        
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
                model="qwen-turbo",
                messages=messages
            )
            
            if response.status_code == 200:
                result = response.output.choices[0].message.content.strip().lower()
                is_complete = "true" in result
                logger.debug(f"Turn complete: {text[:50]}... -> {is_complete}")
                return is_complete
            else:
                logger.warning(f"Turn complete API error: {response.code}")
                # API 错误时使用规则判断
                return self._rule_based_turn_complete(text)
                
        except Exception as e:
            logger.error(f"Turn complete error: {e}")
            return self._rule_based_turn_complete(text)
    
    def _rule_based_turn_complete(self, text: str) -> bool:
        """基于规则的句子完整性判断（备用方案）"""
        text = text.strip().lower()
        
        if not text:
            return False
        
        # 完整句子结束标志
        complete_endings = ['。', '！', '？', '!', '?', '了', '的', '吗', '呢', '吧', '啊', '哦']
        
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
        if len(text) < 8:
            return True
        
        return True
    
    def reset(self):
        """重置对话历史"""
        self.conversation_history = []
        logger.debug("SemanticVAD history reset")
