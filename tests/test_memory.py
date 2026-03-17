import pytest
import asyncio
from aegisos.memory.manager import MemoryManager

@pytest.mark.asyncio
async def test_memory_sliding_window():
    """Test sliding window truncation logic"""
    # Set maximum number of messages to 3
    mem = MemoryManager(max_messages=3, system_prompt="System instructions")
    
    # Initial state: only system prompt
    assert len(mem.history) == 1
    assert mem.history[0].role == "system"

    # Add 1st user message
    await mem.add_message("user", "Hello 1")
    assert len(mem.history) == 2
    
    # Add 2nd user message
    await mem.add_message("user", "Hello 2")
    assert len(mem.history) == 3
    
    # History is full (System + 2 messages)
    # Adding 3rd message should trigger truncation: remove message at index 1 (Hello 1)
    await mem.add_message("user", "Hello 3")
    assert len(mem.history) == 3
    assert mem.history[0].role == "system"
    assert mem.history[1].content == "Hello 2"
    assert mem.history[2].content == "Hello 3"

@pytest.mark.asyncio
async def test_memory_clear():
    """Test clearing memory while retaining System Prompt"""
    mem = MemoryManager(max_messages=10, system_prompt="System instructions")
    await mem.add_message("user", "I want to do X")
    await mem.add_message("assistant", "Sure")
    
    assert len(mem.history) == 3
    mem.clear()
    
    # Only system prompt should remain
    assert len(mem.history) == 1
    assert mem.history[0].role == "system"
    assert mem.get_context() == [{"role": "system", "content": "System instructions"}]
