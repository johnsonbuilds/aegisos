import asyncio
import pytest
import logging
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.dispatcher import AegisDispatcher
from aegisos.core.workspace import WorkspaceManager
from aegisos.core.config import CONFIG

@pytest.mark.asyncio
async def test_dispatcher_system_agent_protection():
    """验证系统代理无法注销"""
    dispatcher = AegisDispatcher()
    system_id = AegisDispatcher.SYSTEM_AGENT_ID
    
    assert system_id in dispatcher.agents
    
    # 尝试注销
    dispatcher.unregister_agent(system_id)
    assert system_id in dispatcher.agents  # 应该依然存在

@pytest.mark.asyncio
async def test_dispatcher_callback_isolation():
    """验证 Agent 回调抛出异常不影响调度器和其他 Agent"""
    dispatcher = AegisDispatcher()
    
    future_b = asyncio.Future()

    async def callback_error(msg: AACPMessage):
        raise RuntimeError("Agent A failed catastrophically!")

    async def callback_ok(msg: AACPMessage):
        future_b.set_result("OK")

    agent_a_id = f"AgentA@{CONFIG.instance_id}"
    agent_b_id = f"AgentB@{CONFIG.instance_id}"
    
    dispatcher.register_agent(agent_a_id, callback_error)
    dispatcher.register_agent(agent_b_id, callback_ok)
    
    await dispatcher.start()

    # 1. 给 AgentA 发送消息（会触发异常）
    msg_a = AACPMessage(sender=f"sys@{CONFIG.instance_id}", receiver=agent_a_id, intent=AACPIntent.INFORM, payload={})
    await dispatcher.send_message(msg_a)

    # 2. 给 AgentB 发送消息（验证依然工作）
    msg_b = AACPMessage(sender=f"sys@{CONFIG.instance_id}", receiver=agent_b_id, intent=AACPIntent.INFORM, payload={})
    await dispatcher.send_message(msg_b)

    result = await asyncio.wait_for(future_b, timeout=1.0)
    assert result == "OK"
    assert dispatcher._is_running  # 调度器应该依然在运行
    
    await dispatcher.stop()

@pytest.mark.asyncio
async def test_dispatcher_duplicate_registration():
    """验证重复注册 Agent 会覆盖之前的回调"""
    dispatcher = AegisDispatcher()
    results = []

    async def callback_1(msg: AACPMessage):
        results.append(1)

    async def callback_2(msg: AACPMessage):
        results.append(2)

    agent_id = f"TargetAgent@{CONFIG.instance_id}"
    dispatcher.register_agent(agent_id, callback_1)
    dispatcher.register_agent(agent_id, callback_2)
    
    await dispatcher.start()
    
    msg = AACPMessage(sender=f"sys@{CONFIG.instance_id}", receiver=agent_id, intent=AACPIntent.INFORM, payload={})
    await dispatcher.send_message(msg)
    
    await asyncio.sleep(0.1)
    assert results == [2]  # 应该只有第二个回调被触发
    
    await dispatcher.stop()

@pytest.mark.asyncio
async def test_workspace_deep_directories(tmp_path):
    """验证深层子目录的自动创建和读取"""
    # 使用 pytest 提供的 tmp_path 避免清理残留
    manager = WorkspaceManager(base_dir=str(tmp_path), session_id="test-deep")
    
    deep_path = "a/b/c/d/test.txt"
    content = "deep content"
    
    # 写入深层目录
    await manager.write_file(deep_path, content)
    
    # 读取验证
    read_content = await manager.read_file(deep_path)
    assert read_content == content
    
    # 验证 list_files 包含该路径
    files = await manager.list_files()
    assert deep_path in files

@pytest.mark.asyncio
async def test_workspace_illegal_paths(tmp_path):
    """验证各种路径穿越变体"""
    manager = WorkspaceManager(base_dir=str(tmp_path), session_id="test-illegal")
    
    bad_paths = [
        "../outside.txt",
        "subdir/../../../etc/passwd",
        "/absolute/path/attempt",
        "C:\\Windows\\System32" if CONFIG.instance_id == "win" else "/dev/null"
    ]
    
    for path in bad_paths:
        with pytest.raises((PermissionError, ValueError)):
            await manager._safe_path(path)
