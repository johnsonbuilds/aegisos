import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.dispatcher import AegisDispatcher
from aegisos.core.llm import OpenAIEngine
from aegisos.agents.base import AACPAgent, AACPResponse
from aegisos.core.config import CONFIG

@pytest.mark.asyncio
async def test_aacp_agent_think_loop():
    # 1. Prepare Mocks
    mock_llm = AsyncMock(spec=OpenAIEngine)
    mock_dispatcher = AsyncMock()
    
    # Mock LLM returning an instruction: reply to the sender
    mock_decision = AACPResponse(
        thought="The user said hi, I should reply.",
        receiver=f"UserAgent@{CONFIG.instance_id}",
        intent=AACPIntent.INFORM,
        payload={"reply": "Hello back!"}
    )
    mock_llm.generate.return_value = mock_decision

    agent = AACPAgent(
        role="assistant",
        agent_id="TestBot",
        llm_engine=mock_llm,
        system_prompt="You are a helpful assistant.",
        dispatcher=mock_dispatcher
    )

    # 2. Mock receiving a message
    incoming_msg = AACPMessage(
        sender=f"UserAgent@{CONFIG.instance_id}",
        receiver=agent.agent_id,
        intent=AACPIntent.REQUEST,
        payload={"query": "hi"}
    )
    
    await agent.handle_message(incoming_msg)

    # 3. Verify results
    # Verify LLM was called correctly (with history and Response Model)
    mock_llm.generate.assert_called_once()
    args, kwargs = mock_llm.generate.call_args
    assert kwargs["response_model"] == AACPResponse
    
    # Verify message history was updated
    assert len(agent.memory.history) == 3 # System + User(hi) + Assistant(thought)

    # Verify Dispatcher received the outgoing AACPMessage
    mock_dispatcher.send_message.assert_called_once()
    sent_msg: AACPMessage = mock_dispatcher.send_message.call_args[0][0]
    assert sent_msg.sender == agent.agent_id
    assert sent_msg.receiver == f"UserAgent@{CONFIG.instance_id}"
    assert sent_msg.payload["reply"] == "Hello back!"
    assert sent_msg.intent == AACPIntent.INFORM


@pytest.mark.asyncio
async def test_aacp_agent_step_guard_unregisters_self():
    original_max_steps = CONFIG.agent_max_steps
    CONFIG.agent_max_steps = 2

    try:
        mock_llm = AsyncMock(spec=OpenAIEngine)
        dispatcher = AegisDispatcher()
        agent = AACPAgent(
            role="assistant",
            agent_id="LoopBot",
            llm_engine=mock_llm,
            system_prompt="You are a looping assistant.",
            dispatcher=dispatcher,
        )
        agent.register_to(dispatcher)

        mock_llm.generate.return_value = AACPResponse(
            thought="Keep trying the same action.",
            receiver=agent.agent_id,
            intent=AACPIntent.REQUEST,
            action={"name": "missing.skill", "args": {}},
            payload={},
        )

        incoming_msg = AACPMessage(
            sender=f"UserAgent@{CONFIG.instance_id}",
            receiver=agent.agent_id,
            intent=AACPIntent.REQUEST,
            payload={"query": "loop"},
        )

        await agent.handle_message(incoming_msg)

        assert agent._is_shutdown is True
        assert agent.agent_id not in dispatcher.agents
        assert mock_llm.generate.await_count == 2
    finally:
        CONFIG.agent_max_steps = original_max_steps


def test_aacp_response_normalizes_null_payload():
    response = AACPResponse.model_validate({
        "thought": "ok",
        "receiver": "worker@local",
        "intent": AACPIntent.INFORM,
        "payload": None,
    })

    assert response.payload == {}


@pytest.mark.asyncio
async def test_agent_injects_structured_skill_metadata():
    mock_llm = AsyncMock(spec=OpenAIEngine)
    mock_llm.generate.return_value = AACPResponse(
        thought="Done.",
        receiver=None,
        intent=AACPIntent.INFORM,
        payload={},
    )

    agent = AACPAgent(
        role="assistant",
        agent_id="SchemaBot",
        llm_engine=mock_llm,
        system_prompt="You are a helpful assistant.",
    )

    incoming_msg = AACPMessage(
        sender="user@local",
        receiver=agent.agent_id,
        intent=AACPIntent.REQUEST,
        payload={"query": "write a file"},
    )

    await agent.handle_message(incoming_msg)

    messages = mock_llm.generate.call_args.kwargs["messages"]
    system_content = messages[0]["content"]
    assert "AVAILABLE SKILLS (JSON):" in system_content
    assert '"name": "core.fs.write"' in system_content
    assert '"path"' in system_content


@pytest.mark.asyncio
async def test_worker_attaches_task_metadata_from_context():
    from aegisos.agents.common import WorkerAgent

    mock_llm = AsyncMock(spec=OpenAIEngine)
    mock_dispatcher = AsyncMock()
    mock_llm.generate.return_value = AACPResponse(
        thought="Task complete.",
        receiver="coordinator@local",
        intent=AACPIntent.INFORM,
        payload={"report_path": "indiehackers_summary.txt"},
    )

    agent = WorkerAgent(
        llm_engine=mock_llm,
        dispatcher=mock_dispatcher,
    )

    incoming_msg = AACPMessage(
        sender="coordinator@local",
        receiver=agent.agent_id,
        intent=AACPIntent.REQUEST,
        payload={"output_path": "indiehackers_summary.txt"},
        context_pointer={
            "type": "plan",
            "uri": "plan.json",
            "current_task": "task_2",
            "expected_revision": 4,
        },
    )

    await agent.handle_message(incoming_msg)

    sent_msg = mock_dispatcher.send_message.call_args[0][0]
    assert sent_msg.payload["task_id"] == "task_2"
    assert sent_msg.payload["expected_revision"] == 4
    assert sent_msg.payload["status"] == "done"
