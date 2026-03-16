import pytest
import asyncio
from aegisos.memory.manager import MemoryManager

@pytest.mark.asyncio
async def test_memory_sliding_window():
    """测试滑动窗口截断逻辑"""
    # 设置最大消息数为 3
    mem = MemoryManager(max_messages=3, system_prompt="System instructions")
    
    # 初始状态：仅有 system prompt
    assert len(mem.history) == 1
    assert mem.history[0].role == "system"

    # 添加第 1 条用户消息
    await mem.add_message("user", "Hello 1")
    assert len(mem.history) == 2
    
    # 添加第 2 条用户消息
    await mem.add_message("user", "Hello 2")
    assert len(mem.history) == 3
    
    # 此时历史已满（System + 2 条消息）
    # 添加第 3 条消息，应触发截断：移除索引为 1 的消息（Hello 1）
    await mem.add_message("user", "Hello 3")
    assert len(mem.history) == 3
    assert mem.history[0].role == "system"
    assert mem.history[1].content == "Hello 2"
    assert mem.history[2].content == "Hello 3"

@pytest.mark.asyncio
async def test_memory_clear():
    """测试清空记忆但保留 System Prompt"""
    mem = MemoryManager(max_messages=10, system_prompt="System instructions")
    await mem.add_message("user", "I want to do X")
    await mem.add_message("assistant", "Sure")
    
    assert len(mem.history) == 3
    mem.clear()
    
    # 应该只剩下 system prompt
    assert len(mem.history) == 1
    assert mem.history[0].role == "system"
    assert mem.get_context() == [{"role": "system", "content": "System instructions"}]
