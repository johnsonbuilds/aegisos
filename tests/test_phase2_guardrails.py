import asyncio
import pytest
import json
import logging
from unittest.mock import AsyncMock, MagicMock
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.dispatcher import AegisDispatcher
from aegisos.core.workspace import WorkspaceManager
from aegisos.core.config import CONFIG
from aegisos.agents.base import AACPAgent, AACPResponse
from aegisos.agents.common import CoordinatorAgent
from aegisos.core.tasks import TaskStatus, Plan, Task

# Configure logging for better visibility during test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_scenario_1_infinite_loop(tmp_path):
    """
    Scenario 1: An agent that keeps reflecting should stop after max_steps.
    """
    workspace = WorkspaceManager(base_dir=str(tmp_path), session_id="scenario-1")
    dispatcher = AegisDispatcher(workspace=workspace)
    await dispatcher.start()

    # Set a small max_steps for testing
    original_max_steps = CONFIG.agent_max_steps
    CONFIG.agent_max_steps = 3

    # Mock LLM to always return a self-reflexion REQUEST
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = AACPResponse(
        thought="I must keep thinking...",
        intent=AACPIntent.REQUEST,
        receiver="loop-agent@local", # Correct role, case-insensitive match should work but let's be safe
        payload={"action": "reflexion"},
        action={"name": "core.exec.code", "args": {"code": "print('loop')"}}
    )

    agent = AACPAgent(
        role="loop-agent",
        llm_engine=mock_llm,
        system_prompt="You are a loop agent.",
        workspace=workspace,
        dispatcher=dispatcher
    )
    agent_id = agent.agent_id
    dispatcher.register_agent(agent_id, agent.handle_message)

    # Trigger the loop
    msg = AACPMessage(
        sender="sys@local",
        receiver=agent_id,
        intent=AACPIntent.INFORM,
        payload={"start": True}
    )
    await dispatcher.send_message(msg)

    # Wait for the agent to hit max steps and unregister
    # 3 steps + some buffer
    for _ in range(10):
        await asyncio.sleep(0.1)
        if agent_id not in dispatcher.agents:
            break
    
    assert agent_id not in dispatcher.agents
    assert agent.current_step > CONFIG.agent_max_steps
    
    # Restore config
    CONFIG.agent_max_steps = original_max_steps
    await dispatcher.stop()

@pytest.mark.asyncio
async def test_scenario_2_timeout(tmp_path):
    """
    Scenario 2: An agent that sleeps longer than task_timeout should be intercepted.
    """
    workspace = WorkspaceManager(base_dir=str(tmp_path), session_id="scenario-2")
    dispatcher = AegisDispatcher(workspace=workspace)
    await dispatcher.start()

    # Set a small timeout for testing
    original_timeout = CONFIG.task_timeout
    CONFIG.task_timeout = 0.5

    async def slow_callback(msg: AACPMessage):
        await asyncio.sleep(2.0) # Longer than timeout

    agent_id = "SlowAgent@local"
    dispatcher.register_agent(agent_id, slow_callback)

    # Capture the error broadcast
    error_future = asyncio.Future()
    async def error_monitor(msg: AACPMessage):
        print(f"Monitor received: {msg.intent} from {msg.sender}")
        if msg.intent == AACPIntent.ERROR:
            err_text = str(msg.payload.get("error", "")).lower()
            print(f"Monitor error text: {err_text}")
            if "timed out" in err_text:
                if not error_future.done():
                    error_future.set_result(msg)
                    print("Monitor set future!")

    # Use a more explicit ID
    monitor_id = f"Monitor@{CONFIG.instance_id}"
    dispatcher.register_agent(monitor_id, error_monitor)

    msg = AACPMessage(
        sender="sys@local",
        receiver=agent_id,
        intent=AACPIntent.INFORM,
        payload={"data": "test"}
    )
    await dispatcher.send_message(msg)

    # Wait for timeout - increase timeout to 5.0 to be safe
    try:
        error_msg = await asyncio.wait_for(error_future, timeout=5.0)
        assert "timed out" in error_msg.payload["error"].lower()
        assert agent_id not in dispatcher.agents # Should be unregistered
    finally:
        CONFIG.task_timeout = original_timeout
        await dispatcher.stop()

@pytest.mark.asyncio
async def test_scenario_3_revision_conflict(tmp_path):
    """
    Scenario 3: Worker tries to update with wrong revision.
    """
    workspace = WorkspaceManager(base_dir=str(tmp_path), session_id="scenario-3")
    dispatcher = AegisDispatcher(workspace=workspace)
    await dispatcher.start()

    # Initialize a plan with revision 1
    plan_data = Plan(
        goal="Test goal",
        tasks=[
            Task(id="task-1", description="Test task", status=TaskStatus.PENDING)
        ],
        revision=1
    )
    await workspace.write_file("plan.json", plan_data.model_dump_json())

    mock_llm = AsyncMock()
    coordinator = CoordinatorAgent(llm_engine=mock_llm, workspace=workspace, dispatcher=dispatcher)
    dispatcher.register_agent(coordinator.agent_id, coordinator.handle_message)

    # Mock a response capture for the error message
    error_future = asyncio.Future()
    async def worker_mock(msg: AACPMessage):
        if msg.intent == AACPIntent.ERROR:
            error_future.set_result(msg)

    worker_id = "Worker@local"
    dispatcher.register_agent(worker_id, worker_mock)

    # Worker sends update with WRONG revision (e.g. 0)
    update_msg = AACPMessage(
        sender=worker_id,
        receiver=coordinator.agent_id,
        intent=AACPIntent.INFORM,
        payload={
            "task_id": "task-1",
            "status": "done",
            "expected_revision": 0  # Should be 1
        }
    )
    await dispatcher.send_message(update_msg)

    # Wait for coordinator to reject
    try:
        error_msg = await asyncio.wait_for(error_future, timeout=2.0)
        assert "cas_or_transition_failure" in error_msg.payload["reason"]
        
        # Verify plan still has revision 1 and task is still pending
        updated_plan_raw = await workspace.read_file("plan.json")
        updated_plan = Plan.model_validate_json(updated_plan_raw)
        assert updated_plan.revision == 1
        assert updated_plan.tasks[0].status == TaskStatus.PENDING
    finally:
        await dispatcher.stop()
