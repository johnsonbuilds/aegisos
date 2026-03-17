import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.dispatcher import AegisDispatcher
from aegisos.agents.base import AACPAgent, AACPResponse
from aegisos.core.llm import BaseLLMEngine
from aegisos.core.config import CONFIG

@pytest.mark.asyncio
async def test_full_agent_lifecycle_integration():
    # 1. Set up Mock LLM and Dispatcher
    mock_llm = AsyncMock(spec=BaseLLMEngine)
    dispatcher = AegisDispatcher(default_llm=mock_llm)
    await dispatcher.start()

    try:
        # 2. Create and register Planner Agent
        planner = AACPAgent(
            role="planner",
            llm_engine=mock_llm,
            system_prompt="You are a planner.",
            dispatcher=dispatcher
        )
        planner.register_to(dispatcher)

        # Prepare Mock LLM response sequence
        # 1st response: Planner's reaction after successful SPAWN (silent)
        # 2nd response: Coder's reaction after receiving a task (reply with code)
        # 3rd response: Planner's reaction after receiving Coder's reply (silent)
        # 4th response: Planner's reaction after successful TERMINATE (silent)
        
        silent_response = AACPResponse(
            thought="Acknowledged.",
            receiver=None, # Break the loop: decide not to take further action
            intent=AACPIntent.INFORM,
            payload={"status": "ack"}
        )

        coder_work_response = AACPResponse(
            thought="I have finished the code.",
            receiver=planner.agent_id,
            intent=AACPIntent.INFORM,
            payload={"code": "print('hello')"}
        )

        mock_llm.generate.side_effect = [
            silent_response,     # Planner receives SPAWN confirmation
            coder_work_response, # Coder receives task
            silent_response,     # Planner receives Coder result
            silent_response      # Planner receives TERMINATE confirmation
        ]

        # 3. Planner requests to spawn a Coder
        spawn_msg = AACPMessage(
            sender=planner.agent_id,
            receiver=dispatcher.SYSTEM_AGENT_ID,
            intent=AACPIntent.SPAWN,
            payload={"role": "coder", "prompt": "You are a coder."}
        )
        
        # Listen for system response
        future_reply = asyncio.Future()

        async def planner_intercept(msg: AACPMessage):
            if msg.sender == dispatcher.SYSTEM_AGENT_ID and msg.intent == AACPIntent.INFORM:
                if msg.payload.get("status") == "SPAWNED":
                    if not future_reply.done():
                        future_reply.set_result(msg)
            # Also call the original handle_message
            await planner.handle_message(msg)

        # Temporarily replace callback to capture response
        dispatcher.register_agent(planner.agent_id, planner_intercept)
        
        await dispatcher.send_message(spawn_msg)
        
        # Wait for system response
        reply_msg = await asyncio.wait_for(future_reply, timeout=2.0)
        assert reply_msg.payload["status"] == "SPAWNED"
        coder_id = reply_msg.payload["agent_id"]
        assert coder_id in dispatcher.agents

        # 4. Planner sends task to Coder
        task_msg = AACPMessage(
            sender=planner.agent_id,
            receiver=coder_id,
            intent=AACPIntent.REQUEST,
            payload={"task": "write hello world"}
        )

        # Listen for Coder's reply (by observing messages received by Planner)
        future_coder_reply = asyncio.Future()
        
        async def planner_intercept_task(msg: AACPMessage):
            if msg.sender == coder_id and msg.intent == AACPIntent.INFORM:
                if not future_coder_reply.done():
                    future_coder_reply.set_result(msg)
            await planner.handle_message(msg)
        
        dispatcher.register_agent(planner.agent_id, planner_intercept_task)
        await dispatcher.send_message(task_msg)

        coder_reply = await asyncio.wait_for(future_coder_reply, timeout=2.0)
        assert coder_reply.payload["code"] == "print('hello')"

        # 5. Planner terminates Coder
        terminate_msg = AACPMessage(
            sender=planner.agent_id,
            receiver=dispatcher.SYSTEM_AGENT_ID,
            intent=AACPIntent.TERMINATE,
            payload={"agent_id": coder_id}
        )
        
        # Listen for termination confirmation
        future_term_reply = asyncio.Future()
        async def planner_intercept_term(msg: AACPMessage):
            if msg.sender == dispatcher.SYSTEM_AGENT_ID and msg.payload.get("status") == "TERMINATED":
                if not future_term_reply.done():
                    future_term_reply.set_result(msg)
            await planner.handle_message(msg)
        
        dispatcher.register_agent(planner.agent_id, planner_intercept_term)
        await dispatcher.send_message(terminate_msg)
        
        await asyncio.wait_for(future_term_reply, timeout=2.0)
        assert coder_id not in dispatcher.agents

    finally:
        await dispatcher.stop()
