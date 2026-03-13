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
    # 1. 设置 Mock LLM 和 Dispatcher
    mock_llm = AsyncMock(spec=BaseLLMEngine)
    dispatcher = AegisDispatcher(default_llm=mock_llm)
    await dispatcher.start()

    try:
        # 2. 创建并注册 Planner Agent
        planner = AACPAgent(
            role="planner",
            llm_engine=mock_llm,
            system_prompt="You are a planner.",
            dispatcher=dispatcher
        )
        planner.register_to(dispatcher)

        # 准备 Mock LLM 的响应序列
        # 第一个响应：Planner 收到 SPAWN 成功后的反应 (静默)
        # 第二个响应：Coder 收到任务后的反应 (回复代码)
        # 第三个响应：Planner 收到 Coder 回复后的反应 (静默)
        # 第四个响应：Planner 收到 TERMINATE 成功后的反应 (静默)
        
        silent_response = AACPResponse(
            thought="Acknowledged.",
            receiver=None, # 打破循环：决定不采取进一步行动
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
            silent_response,     # Planner 收到 SPAWN 确认
            coder_work_response, # Coder 收到任务
            silent_response,     # Planner 收到 Coder 结果
            silent_response      # Planner 收到 TERMINATE 确认
        ]

        # 3. Planner 请求孵化一个 Coder
        spawn_msg = AACPMessage(
            sender=planner.agent_id,
            receiver=dispatcher.SYSTEM_AGENT_ID,
            intent=AACPIntent.SPAWN,
            payload={"role": "coder", "prompt": "You are a coder."}
        )
        
        # 监听系统回复
        future_reply = asyncio.Future()

        async def planner_intercept(msg: AACPMessage):
            if msg.sender == dispatcher.SYSTEM_AGENT_ID and msg.intent == AACPIntent.INFORM:
                if msg.payload.get("status") == "SPAWNED":
                    if not future_reply.done():
                        future_reply.set_result(msg)
            # 同时也调用原来的 handle_message
            await planner.handle_message(msg)

        # 临时替换 callback 以捕获回复
        dispatcher.register_agent(planner.agent_id, planner_intercept)
        
        await dispatcher.send_message(spawn_msg)
        
        # 等待系统回复
        reply_msg = await asyncio.wait_for(future_reply, timeout=2.0)
        assert reply_msg.payload["status"] == "SPAWNED"
        coder_id = reply_msg.payload["agent_id"]
        assert coder_id in dispatcher.agents

        # 4. Planner 给 Coder 发送任务
        task_msg = AACPMessage(
            sender=planner.agent_id,
            receiver=coder_id,
            intent=AACPIntent.REQUEST,
            payload={"task": "write hello world"}
        )

        # 监听 Coder 的回复 (通过观察 Planner 收到的消息)
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

        # 5. Planner 销毁 Coder
        terminate_msg = AACPMessage(
            sender=planner.agent_id,
            receiver=dispatcher.SYSTEM_AGENT_ID,
            intent=AACPIntent.TERMINATE,
            payload={"agent_id": coder_id}
        )
        
        # 监听销毁确认
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
