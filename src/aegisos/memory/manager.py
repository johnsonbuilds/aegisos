import logging
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("MemoryManager")

class MemoryItem(BaseModel):
    """单条记忆条目"""
    role: str
    content: str
    tokens: int = 0
    important: bool = False

class MemoryManager:
    """
    负责 Agent 的认知记忆管理。
    当前实现：基于消息轮数和 Token 计数的滑动窗口（热记忆）。
    """
    def __init__(
        self, 
        max_messages: int = 15, 
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None
    ):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        
        # 热记忆存储
        self.history: List[MemoryItem] = []
        
        # 如果提供了 system_prompt，它将作为永久记忆保留在最前面
        if system_prompt:
            self.history.append(MemoryItem(role="system", content=system_prompt, important=True))

    async def add_message(self, role: str, content: str, tokens: int = 0):
        """
        向历史记录中添加一条消息。
        """
        item = MemoryItem(role=role, content=content, tokens=tokens)
        self.history.append(item)
        await self._enforce_limits()

    async def _enforce_limits(self):
        """
        实施截断逻辑，确保历史不超出限制。
        保留索引为 0 的 system prompt（如果存在）。
        """
        # 1. 基于消息数量的截断
        # 如果有 system prompt，我们保留 history[0]，从 history[1] 开始截断
        has_system = len(self.history) > 0 and self.history[0].role == "system"
        start_idx = 1 if has_system else 0
        
        while len(self.history) > self.max_messages:
            if len(self.history) > start_idx:
                removed = self.history.pop(start_idx)
                logger.debug(f"MemoryManager: Removed old message from {removed.role}")
            else:
                break

        # 2. TODO: 基于 Token 计数的精细截断 (需要集成 tiktoken)
        # 目前仅实现简单的轮数截断作为 MVP

    def get_context(self) -> List[Dict[str, str]]:
        """
        返回适合 LLM 消费的列表格式。
        """
        return [{"role": item.role, "content": item.content} for item in self.history]

    def clear(self):
        """清空除 System Prompt 以外的所有历史"""
        has_system = len(self.history) > 0 and self.history[0].role == "system"
        if has_system:
            self.history = [self.history[0]]
        else:
            self.history = []
