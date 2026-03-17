import asyncio
import pytest
import logging
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.dispatcher import AegisDispatcher
from aegisos.core.workspace import WorkspaceManager
from aegisos.core.config import CONFIG

@pytest.mark.asyncio
async def test_dispatcher_system_agent_protection():
    """Verify that system agents cannot be unregistered"""
    dispatcher = AegisDispatcher()
    system_id = AegisDispatcher.SYSTEM_AGENT_ID
    
    assert system_id in dispatcher.agents
    
    # Attempt to unregister
    dispatcher.unregister_agent(system_id)
    assert system_id in dispatcher.agents  # Should still exist

@pytest.mark.asyncio
async def test_dispatcher_callback_isolation():
    """Verify that an Agent callback throwing an exception does not affect the dispatcher or other Agents"""
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

    # 1. Send message to AgentA (will trigger an exception)
    msg_a = AACPMessage(sender=f"sys@{CONFIG.instance_id}", receiver=agent_a_id, intent=AACPIntent.INFORM, payload={})
    await dispatcher.send_message(msg_a)

    # 2. Send message to AgentB (verify it still works)
    msg_b = AACPMessage(sender=f"sys@{CONFIG.instance_id}", receiver=agent_b_id, intent=AACPIntent.INFORM, payload={})
    await dispatcher.send_message(msg_b)

    result = await asyncio.wait_for(future_b, timeout=1.0)
    assert result == "OK"
    assert dispatcher._is_running  # Dispatcher should still be running
    
    await dispatcher.stop()

@pytest.mark.asyncio
async def test_dispatcher_duplicate_registration():
    """Verify that duplicate Agent registration overrides the previous callback"""
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
    assert results == [2]  # Only the second callback should be triggered
    
    await dispatcher.stop()

@pytest.mark.asyncio
async def test_workspace_deep_directories(tmp_path):
    """Verify automatic creation and reading of deep subdirectories"""
    # Use tmp_path provided by pytest to avoid leftover cleanup issues
    manager = WorkspaceManager(base_dir=str(tmp_path), session_id="test-deep")
    
    deep_path = "a/b/c/d/test.txt"
    content = "deep content"
    
    # Write to a deep directory
    await manager.write_file(deep_path, content)
    
    # Verify reading
    read_content = await manager.read_file(deep_path)
    assert read_content == content
    
    # Verify that list_files contains the path
    files = await manager.list_files()
    assert deep_path in files

@pytest.mark.asyncio
async def test_workspace_illegal_paths(tmp_path):
    """Verify various path traversal variants"""
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
