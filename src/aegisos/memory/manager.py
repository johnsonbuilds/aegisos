import logging
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("MemoryManager")

class MemoryItem(BaseModel):
    """A single memory item."""
    role: str
    content: str
    tokens: int = 0
    important: bool = False

class MemoryManager:
    """
    Responsible for Agent's cognitive memory management.
    Current implementation: sliding window based on message rounds and token count (hot memory).
    """
    def __init__(
        self, 
        max_messages: int = 15, 
        max_tokens: int = 4000,
        system_prompt: Optional[str] = None
    ):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        
        # Hot memory storage
        self.history: List[MemoryItem] = []
        
        # If system_prompt is provided, it will be kept at the beginning as a permanent memory.
        if system_prompt:
            self.history.append(MemoryItem(role="system", content=system_prompt, important=True))

    async def add_message(self, role: str, content: str, tokens: int = 0):
        """
        Add a message to the history.
        """
        item = MemoryItem(role=role, content=content, tokens=tokens)
        self.history.append(item)
        await self._enforce_limits()

    async def _enforce_limits(self):
        """
        Implement truncation logic to ensure history does not exceed limits.
        Keep the system prompt at index 0 (if it exists).
        """
        # 1. Truncation based on message count
        # If there's a system prompt, we keep history[0] and truncate starting from history[1].
        has_system = len(self.history) > 0 and self.history[0].role == "system"
        start_idx = 1 if has_system else 0
        
        while len(self.history) > self.max_messages:
            if len(self.history) > start_idx:
                removed = self.history.pop(start_idx)
                logger.debug(f"MemoryManager: Removed old message from {removed.role}")
            else:
                break

        # 2. TODO: Fine-grained truncation based on token count (needs tiktoken integration)
        # Currently only simple message round truncation is implemented as an MVP.

    def get_context(self) -> List[Dict[str, str]]:
        """
        Return list format suitable for LLM consumption.
        """
        return [{"role": item.role, "content": item.content} for item in self.history]

    def clear(self):
        """Clear all history except for the System Prompt."""
        has_system = len(self.history) > 0 and self.history[0].role == "system"
        if has_system:
            self.history = [self.history[0]]
        else:
            self.history = []
