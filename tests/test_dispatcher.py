import asyncio
import json
import pytest
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.dispatcher import AegisDispatcher
from aegisos.core.config import CONFIG
from aegisos.core.workspace import WorkspaceManager

@pytest.mark.asyncio
async def test_dispatcher_routing():
    dispatcher = AegisDispatcher()
    
    # Future to capture callback messages
    future_a = asyncio.Future()
    future_b = asyncio.Future()

    async def callback_a(msg: AACPMessage):
        future_a.set_result(msg)

    async def callback_b(msg: AACPMessage):
        future_b.set_result(msg)

    agent_a_uri = f"AgentA@{CONFIG.instance_id}"
    agent_b_uri = f"AgentB@{CONFIG.instance_id}"
    system_uri = f"System@{CONFIG.instance_id}"

    dispatcher.register_agent(agent_a_uri, callback_a)
    dispatcher.register_agent(agent_b_uri, callback_b)

    # Start the dispatcher
    await dispatcher.start()

    # 1. Send a unicast message to AgentB
    msg_to_b = AACPMessage(
        sender=agent_a_uri,
        receiver=agent_b_uri,
        intent=AACPIntent.REQUEST,
        payload={"data": "test_unicast"}
    )
    await dispatcher.send_message(msg_to_b)

    # Wait for results
    received_msg_b = await asyncio.wait_for(future_b, timeout=1.0)
    assert received_msg_b.payload["data"] == "test_unicast"
    assert not future_a.done()

    # 2. Send a broadcast message
    # Reset Futures
    future_a = asyncio.Future()
    future_b = asyncio.Future()
    
    msg_broadcast = AACPMessage(
        sender=system_uri,
        receiver="BROADCAST",
        intent=AACPIntent.INFORM,
        payload={"data": "test_broadcast"}
    )
    await dispatcher.send_message(msg_broadcast)

    await asyncio.gather(
        asyncio.wait_for(future_a, timeout=1.0),
        asyncio.wait_for(future_b, timeout=1.0)
    )
    
    assert future_a.result().payload["data"] == "test_broadcast"
    assert future_b.result().payload["data"] == "test_broadcast"

    # Stop the dispatcher
    await dispatcher.stop()

@pytest.mark.asyncio
async def test_dispatcher_invalid_target(tmp_path):
    workspace = WorkspaceManager(base_dir=str(tmp_path), session_id="trace-drop")
    dispatcher = AegisDispatcher(workspace=workspace)
    await dispatcher.start()

    # Send to a non-existent Agent
    msg = AACPMessage(
        sender=f"AgentA@{CONFIG.instance_id}",
        receiver=f"Unknown@{CONFIG.instance_id}",
        intent=AACPIntent.REQUEST,
        payload={}
    )
    await dispatcher.send_message(msg)
    
    # Wait a moment to ensure the message is processed
    await asyncio.sleep(0.1)
    
    await dispatcher.stop()
    trace_content = await workspace.read_file("logs/message_trace.jsonl")
    entries = [json.loads(line) for line in trace_content.splitlines() if line.strip()]

    assert any(entry["event"] == "queued" for entry in entries)
    assert any(entry["event"] == "local-delivery-failed" for entry in entries)
    assert all(entry["session_id"] == "trace-drop" for entry in entries)

@pytest.mark.asyncio
async def test_dispatcher_persists_message_trace(tmp_path):
    workspace = WorkspaceManager(base_dir=str(tmp_path), session_id="trace-session")
    dispatcher = AegisDispatcher(workspace=workspace)

    future_receiver = asyncio.Future()

    async def callback_receiver(msg: AACPMessage):
        future_receiver.set_result(msg)

    sender_uri = f"sender@{CONFIG.instance_id}"
    receiver_uri = f"receiver@{CONFIG.instance_id}"
    dispatcher.register_agent(receiver_uri, callback_receiver)

    await dispatcher.start()
    try:
        msg = AACPMessage(
            sender=sender_uri,
            receiver=receiver_uri,
            intent=AACPIntent.REQUEST,
            payload={"data": "trace-me"},
            context_pointer={"type": "plan", "uri": "plan.json", "current_task": "task_1"}
        )
        await dispatcher.send_message(msg)

        received_msg = await asyncio.wait_for(future_receiver, timeout=1.0)
        assert received_msg.payload["data"] == "trace-me"
    finally:
        await dispatcher.stop()

    trace_content = await workspace.read_file("logs/message_trace.jsonl")
    entries = [json.loads(line) for line in trace_content.splitlines() if line.strip()]

    assert len(entries) >= 2
    queued_entry = next(entry for entry in entries if entry["event"] == "queued")
    delivered_entry = next(entry for entry in entries if entry["event"] == "delivered")

    assert queued_entry["message_id"] == delivered_entry["message_id"]
    assert queued_entry["sender"] == sender_uri
    assert queued_entry["receiver"] == receiver_uri
    assert queued_entry["intent"] == AACPIntent.REQUEST.value
    assert queued_entry["session_id"] == "trace-session"
    assert queued_entry["task_id"] == "task_1"
    assert delivered_entry["resolved_receiver"] == receiver_uri
