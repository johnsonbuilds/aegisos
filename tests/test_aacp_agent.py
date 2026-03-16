import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.llm import OpenAIEngine
from aegisos.agents.base import AACPAgent, AACPResponse
from aegisos.core.config import CONFIG

@pytest.mark.asyncio
async def test_aacp_agent_think_loop():
    # 1. 准备 Mock
    mock_llm = AsyncMock(spec=OpenAIEngine)
    mock_dispatcher = AsyncMock()
    
    # 模拟 LLM 返回一个指令：回复消息给发送者
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

    # 2. 模拟收到一条消息
    incoming_msg = AACPMessage(
        sender=f"UserAgent@{CONFIG.instance_id}",
        receiver=agent.agent_id,
        intent=AACPIntent.REQUEST,
        payload={"query": "hi"}
    )
    
    await agent.handle_message(incoming_msg)

    # 3. 验证结果
    # 验证 LLM 被正确调用（带着历史记录和 Response Model）
    mock_llm.generate.assert_called_once()
    args, kwargs = mock_llm.generate.call_args
    assert kwargs["response_model"] == AACPResponse
    
    # 验证消息历史已更新
    assert len(agent.memory.history) == 3 # System + User(hi) + Assistant(thought)

    # 验证 Dispatcher 收到了传出的 AACPMessage
    mock_dispatcher.send_message.assert_called_once()
    sent_msg: AACPMessage = mock_dispatcher.send_message.call_args[0][0]
    assert sent_msg.sender == agent.agent_id
    assert sent_msg.receiver == f"UserAgent@{CONFIG.instance_id}"
    assert sent_msg.payload["reply"] == "Hello back!"
    assert sent_msg.intent == AACPIntent.INFORM
