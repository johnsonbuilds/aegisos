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
    Test Agent's self-executing reflection loop:
    1. Receive task
    2. Execute code
    3. Obtain results and provide final response
    """
    mock_llm = AsyncMock()
    mock_dispatcher = AsyncMock()
    
    # Define LLM's two-step response
    # Step 1: Decide to execute code (using the new action field)
    res1 = AACPResponse(
        thought="I need to calculate 2+2 using Python.",
        receiver="coder@local",
        intent=AACPIntent.REQUEST,
        action=AACPAction.CODE_EXEC,
        payload={"code": "print(2+2)"}
    )
    # Step 2: Observe results and reply
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

    # Mock receiving the initial task
    task_msg = AACPMessage(
        sender="user@local",
        receiver="coder@local",
        intent=AACPIntent.REQUEST,
        payload={"task": "Calculate 2+2"}
    )

    # Trigger processing
    await agent.handle_message(task_msg)

    # Verify logic
    # 1. LLM should be called twice (first to think about the task, second after seeing the execution result)
    assert mock_llm.generate.call_count == 2
    
    # 2. Check if memory contains the execution result
    # Memory order: [System, User(Task), Assistant(Thought1), User(Result)]
    history = agent.memory.history
    assert any("EXECUTION_RESULT" in item.content for item in history)
    assert any("4" in item.content for item in history)

    # 3. Verify if an INFORM message was eventually sent to the user
    sent_msgs = [call.args[0] for call in mock_dispatcher.send_message.call_args_list]
    assert any(m.intent == AACPIntent.INFORM and m.payload["result"] == "4" for m in sent_msgs)
    logger = MagicMock() # Used for observation in tests
