import pytest
from unittest.mock import AsyncMock, MagicMock
from aegisos.agents.base import AACPAgent, AACPResponse
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.actions import AACPAction
from aegisos.core.workspace import WorkspaceManager
import os
import shutil

@pytest.fixture
def workspace():
    path = "_test_reflexion_workspace"
    if os.path.exists(path):
        shutil.rmtree(path)
    ws = WorkspaceManager(path, session_id="test-reflexion")
    yield ws
    if os.path.exists(path):
        shutil.rmtree(path)

@pytest.mark.asyncio
async def test_agent_reflexion_loop(workspace):
    """
    测试 Agent 的自执行反思闭环：
    1. 接收任务
    2. 执行代码
    3. 获取结果并最终回复
    """
    mock_llm = AsyncMock()
    mock_dispatcher = AsyncMock()
    
    # 定义 LLM 的两步反应
    # 第一步：决定执行代码 (使用新的 action 字段)
    res1 = AACPResponse(
        thought="I need to calculate 2+2 using Python.",
        receiver="coder@local",
        intent=AACPIntent.REQUEST,
        action=AACPAction.CODE_EXEC,
        payload={"code": "print(2+2)"}
    )
    # 第二步：看到结果并回复
    res2 = AACPResponse(
        thought="The result is 4. I will inform the user.",
        receiver="user@local",
        intent=AACPIntent.INFORM,
        payload={"result": "4"}
    )
    
    mock_llm.generate.side_effect = [res1, res2]

    agent = AACPAgent(
        role="coder",
        agent_id="coder@local",
        llm_engine=mock_llm,
        system_prompt="You are a coder.",
        dispatcher=mock_dispatcher,
        workspace=workspace
    )

    # 模拟收到初始任务
    task_msg = AACPMessage(
        sender="user@local",
        receiver="coder@local",
        intent=AACPIntent.REQUEST,
        payload={"task": "Calculate 2+2"}
    )

    # 触发处理
    await agent.handle_message(task_msg)

    # 验证逻辑
    # 1. LLM 应该被调用了两次（第一次思考任务，第二次看到执行结果后思考）
    assert mock_llm.generate.call_count == 2
    
    # 2. 检查记忆中是否包含了执行结果
    # 记忆顺序: [System, User(Task), Assistant(Thought1), User(Result)]
    history = agent.memory.history
    assert any("EXECUTION_RESULT" in item.content for item in history)
    assert any("4" in item.content for item in history)

    # 3. 验证最终是否发出了 INFORM 消息给用户
    sent_msgs = [call.args[0] for call in mock_dispatcher.send_message.call_args_list]
    assert any(m.intent == AACPIntent.INFORM and m.payload["result"] == "4" for m in sent_msgs)
    logger = MagicMock() # 用于在测试中观察
