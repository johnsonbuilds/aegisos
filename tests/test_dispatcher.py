import asyncio
import pytest
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.dispatcher import AegisDispatcher
from aegisos.core.config import CONFIG

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
async def test_dispatcher_invalid_target():
    dispatcher = AegisDispatcher()
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
    # Currently mainly verifies it won't crash and will log the event
