import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.agents.base import AACPAgent, AACPResponse
from aegisos.core.llm import BaseLLMEngine
from aegisos.core.workspace import WorkspaceManager
from aegisos.agents.common import CoordinatorAgent, WorkerAgent
from pathlib import Path

class MockLLM(BaseLLMEngine):
    def __init__(self):
        self.last_messages = []
        self.call_count = 0

    async def generate(self, messages, response_model=None):
        self.last_messages = messages
        self.call_count += 1
        if response_model == AACPResponse:
            return AACPResponse(
                thought="Testing cognitive architecture",
                receiver="receiver@local",
                intent=AACPIntent.REQUEST,
                action={"name": "core.fs.write", "args": {"path": "test.txt", "content": "hello"}},
                context_pointer={"type": "plan", "uri": "plan.json", "current_task": "task_1"}
            )
        return "mock response"

@pytest.mark.asyncio
async def test_structured_context_pointer_and_auto_inspection(tmp_path):
    # Setup workspace
    workspace = WorkspaceManager(tmp_path)
    plan_file = workspace.root_path / "plan.json"
    plan_content = {"status": "in_progress", "tasks": []}
    plan_file.write_text(json.dumps(plan_content))
    
    # Setup agent
    llm = MockLLM()
    agent = AACPAgent(
        role="test_agent",
        llm_engine=llm,
        system_prompt="You are a test agent.",
        workspace=workspace
    )
    
    # Mock dispatcher
    dispatcher = MagicMock()
    dispatcher.send_message = AsyncMock()
    agent.register_to(dispatcher)
    
    # Create message with structured context_pointer
    msg = AACPMessage(
        sender="coordinator@local",
        receiver=agent.agent_id,
        intent=AACPIntent.REQUEST,
        payload={"dummy": "data"},
        context_pointer={"type": "plan", "uri": "plan.json", "current_task": "task_1"}
    )
    
    # Handle message (this triggers think)
    await agent.handle_message(msg)
    
    # Verify Lazy Cognitive Loading: The last user message should NOT contain full file content
    last_msg = llm.last_messages[-1]["content"]
    assert "EXTERNAL_STATE_CONTENT" not in last_msg
    assert "[COGNITIVE CONTEXT INDEX]" in last_msg
    assert "Directive: task_1" in last_msg
    assert "Available State Reference: plan.json" in last_msg
    
    # Verify Structured Payload Enforcement in out-going message
    sent_msg = dispatcher.send_message.call_args[0][0]
    assert sent_msg.intent == AACPIntent.REQUEST
    assert sent_msg.payload["action"]["name"] == "core.fs.write"
    assert sent_msg.payload["action"]["args"]["path"] == "test.txt"
    assert isinstance(sent_msg.context_pointer, dict)
    assert sent_msg.context_pointer["current_task"] == "task_1"


@pytest.mark.asyncio
async def test_coordinator_updates_plan_without_llm(tmp_path):
    workspace = WorkspaceManager(tmp_path)
    await workspace.write_file(
        "plan.json",
        json.dumps({
            "goal": "demo",
            "revision": 0,
            "tasks": [{
                "id": "task_1",
                "description": "demo task",
                "status": "running",
                "revision": 0,
            }],
        })
    )

    llm = AsyncMock()
    dispatcher = MagicMock()
    dispatcher.send_message = AsyncMock()
    coordinator = CoordinatorAgent(llm_engine=llm, workspace=workspace, dispatcher=dispatcher)

    message = AACPMessage(
        sender="worker@local",
        receiver=coordinator.agent_id,
        intent=AACPIntent.INFORM,
        payload={
            "task_id": "task_1",
            "status": "done",
            "result": {"summary": "ok"},
            "expected_revision": 0,
        },
    )

    await coordinator.handle_message(message)

    llm.generate.assert_not_called()
    dispatcher.send_message.assert_not_called()

    plan = json.loads(await workspace.read_file("plan.json"))
    assert plan["revision"] == 1
    assert plan["tasks"][0]["status"] == "done"
    assert plan["tasks"][0]["revision"] == 1
    assert plan["tasks"][0]["result"] == {"summary": "ok"}


@pytest.mark.asyncio
async def test_coordinator_rejects_missing_expected_revision_without_llm(tmp_path):
    workspace = WorkspaceManager(tmp_path)
    initial_plan = {
        "goal": "demo",
        "revision": 0,
        "tasks": [{
            "id": "task_1",
            "description": "demo task",
            "status": "running",
            "revision": 0,
        }],
    }
    await workspace.write_file("plan.json", json.dumps(initial_plan))

    llm = AsyncMock()
    dispatcher = MagicMock()
    dispatcher.send_message = AsyncMock()
    coordinator = CoordinatorAgent(llm_engine=llm, workspace=workspace, dispatcher=dispatcher)

    message = AACPMessage(
        sender="worker@local",
        receiver=coordinator.agent_id,
        intent=AACPIntent.INFORM,
        payload={
            "task_id": "task_1",
            "status": "done",
            "result": {"summary": "ok"},
        },
    )

    await coordinator.handle_message(message)

    llm.generate.assert_not_called()
    dispatcher.send_message.assert_called_once()

    error_msg = dispatcher.send_message.call_args[0][0]
    assert error_msg.receiver == "worker@local"
    assert error_msg.intent == AACPIntent.ERROR
    assert error_msg.payload["task_id"] == "task_1"
    assert error_msg.payload["reason"] == "missing_expected_revision"

    plan = json.loads(await workspace.read_file("plan.json"))
    assert plan == initial_plan


@pytest.mark.asyncio
async def test_coordinator_accepts_explicit_cas_bypass(tmp_path):
    workspace = WorkspaceManager(tmp_path)
    await workspace.write_file(
        "plan.json",
        json.dumps({
            "goal": "demo",
            "revision": 0,
            "tasks": [{
                "id": "task_1",
                "description": "demo task",
                "status": "running",
                "revision": 3,
            }],
        })
    )

    llm = AsyncMock()
    dispatcher = MagicMock()
    dispatcher.send_message = AsyncMock()
    coordinator = CoordinatorAgent(llm_engine=llm, workspace=workspace, dispatcher=dispatcher)

    message = AACPMessage(
        sender="worker@local",
        receiver=coordinator.agent_id,
        intent=AACPIntent.INFORM,
        payload={
            "task_id": "task_1",
            "status": "done",
            "result": {"summary": "ok"},
            "expected_revision": -1,
        },
    )

    await coordinator.handle_message(message)

    llm.generate.assert_not_called()
    dispatcher.send_message.assert_not_called()

    plan = json.loads(await workspace.read_file("plan.json"))
    assert plan["revision"] == 1
    assert plan["tasks"][0]["status"] == "done"
    assert plan["tasks"][0]["revision"] == 4


@pytest.mark.asyncio
async def test_coordinator_dispatches_next_pending_task_after_update(tmp_path):
    workspace = WorkspaceManager(tmp_path)
    await workspace.write_file(
        "plan.json",
        json.dumps({
            "goal": "demo",
            "revision": 0,
            "tasks": [
                {
                    "id": "task_1",
                    "description": "Fetch source content",
                    "status": "running",
                    "role": "web_scraper",
                    "revision": 0,
                },
                {
                    "id": "task_2",
                    "description": "Generate summary report",
                    "status": "pending",
                    "role": "analyst",
                    "revision": 0,
                },
            ],
        })
    )

    llm = AsyncMock()

    class DummyDispatcher:
        def __init__(self):
            self.agents = {"analyst@local": AsyncMock()}
            self.messages = []

        async def send_message(self, message):
            self.messages.append(message)

        def resolve_target(self, target_uri):
            return target_uri

    dispatcher = DummyDispatcher()
    coordinator = CoordinatorAgent(llm_engine=llm, workspace=workspace, dispatcher=dispatcher)

    message = AACPMessage(
        sender="worker@local",
        receiver=coordinator.agent_id,
        intent=AACPIntent.INFORM,
        payload={
            "task_id": "task_1",
            "status": "done",
            "result": {"context_pointer": "downloads/source.md"},
            "expected_revision": 0,
        },
    )

    await coordinator.handle_message(message)

    llm.generate.assert_not_called()
    assert len(dispatcher.messages) == 1
    dispatch_msg = dispatcher.messages[0]
    assert dispatch_msg.receiver == "analyst@local"
    assert dispatch_msg.payload["input_context_pointer"] == "downloads/source.md"
    assert dispatch_msg.payload["output_path"] == "indiehackers_summary.txt"
    assert "task_description" not in dispatch_msg.payload
    assert "task_role" not in dispatch_msg.payload
    assert dispatch_msg.context_pointer["current_task"] == "task_2"
    assert dispatch_msg.context_pointer["expected_revision"] == 0
    assert set(dispatch_msg.context_pointer.keys()) == {"type", "uri", "current_task", "expected_revision"}

    updated_plan = json.loads(await workspace.read_file("plan.json"))
    assert updated_plan["tasks"][0]["status"] == "done"
    assert updated_plan["tasks"][1]["status"] == "running"
    assert updated_plan["tasks"][1]["assignee"] == "analyst@local"


@pytest.mark.asyncio
async def test_coordinator_normalizes_llm_worker_dispatch(tmp_path):
    workspace = WorkspaceManager(tmp_path)
    await workspace.write_file(
        "plan.json",
        json.dumps({
            "goal": "demo",
            "revision": 0,
            "tasks": [
                {
                    "id": "task_1",
                    "description": "Scrape the target page",
                    "status": "pending",
                    "role": "web_scraper",
                    "revision": 0,
                }
            ],
        })
    )

    llm = AsyncMock()
    llm.generate.return_value = AACPResponse(
        thought="Dispatch work",
        receiver="web_scraper@local",
        intent=AACPIntent.REQUEST,
        action={"name": "core.web.scrape", "args": {"url": "https://example.com"}},
        payload={},
        context_pointer="plan.json",
    )

    class DummyDispatcher:
        SYSTEM_AGENT_ID = "system@local-node"

        def __init__(self):
            self.agents = {"web_scraper@local": AsyncMock()}
            self.messages = []

        async def send_message(self, message):
            self.messages.append(message)

        def resolve_target(self, target_uri):
            return target_uri

    dispatcher = DummyDispatcher()
    coordinator = CoordinatorAgent(llm_engine=llm, workspace=workspace, dispatcher=dispatcher)

    incoming_msg = AACPMessage(
        sender="user@local",
        receiver=coordinator.agent_id,
        intent=AACPIntent.INFORM,
        payload={"goal": "demo"},
    )

    await coordinator.handle_message(incoming_msg)

    assert len(dispatcher.messages) == 1
    dispatch_msg = dispatcher.messages[0]
    assert dispatch_msg.receiver == "web_scraper@local"
    assert "action" not in dispatch_msg.payload
    assert "task_description" not in dispatch_msg.payload
    assert "task_role" not in dispatch_msg.payload
    assert isinstance(dispatch_msg.context_pointer, dict)
    assert dispatch_msg.context_pointer["current_task"] == "task_1"
    assert dispatch_msg.context_pointer["expected_revision"] == 0
    assert set(dispatch_msg.context_pointer.keys()) == {"type", "uri", "current_task", "expected_revision"}

    updated_plan = json.loads(await workspace.read_file("plan.json"))
    assert updated_plan["tasks"][0]["status"] == "running"
    assert updated_plan["tasks"][0]["assignee"] == "web_scraper@local"


@pytest.mark.asyncio
async def test_worker_executes_plan_based_artifact_task(tmp_path):
    workspace = WorkspaceManager(tmp_path)
    await workspace.write_file(
        "plan.json",
        json.dumps(
            {
                "goal": "demo",
                "revision": 4,
                "tasks": [
                    {
                        "id": "task_1",
                        "description": "Fetch source content",
                        "status": "done",
                        "role": "web_scraper",
                        "revision": 1,
                        "result": {"context_pointer": "downloads/source.md"},
                    },
                    {
                        "id": "task_2",
                        "description": "Analyze the scraped content and generate a short summary report",
                        "status": "running",
                        "role": "analyst",
                        "assignee": "analyst@local",
                        "revision": 0,
                    },
                ],
            }
        ),
    )
    await workspace.write_file("downloads/source.md", "Headline A\nHeadline B\nHeadline C")

    llm = AsyncMock()
    llm.generate.return_value = "Summary Title\n- Headline A\n- Headline B\nConclusion"

    class DummyDispatcher:
        def __init__(self):
            self.messages = []

        async def send_message(self, message):
            self.messages.append(message)

    dispatcher = DummyDispatcher()
    worker = WorkerAgent(llm_engine=llm, workspace=workspace, dispatcher=dispatcher)

    message = AACPMessage(
        sender="coordinator@local",
        receiver="analyst@local",
        intent=AACPIntent.REQUEST,
        payload={
            "input_context_pointer": "downloads/source.md",
            "output_path": "indiehackers_summary.txt",
        },
        context_pointer={
            "type": "plan",
            "uri": "plan.json",
            "current_task": "task_2",
            "expected_revision": 0,
        },
    )

    await worker.handle_message(message)

    llm.generate.assert_called_once()
    assert await workspace.read_file("indiehackers_summary.txt") == "Summary Title\n- Headline A\n- Headline B\nConclusion"
    assert len(dispatcher.messages) == 1
    result_msg = dispatcher.messages[0]
    assert result_msg.intent == AACPIntent.INFORM
    assert result_msg.payload["task_id"] == "task_2"
    assert result_msg.payload["expected_revision"] == 0
    assert result_msg.payload["status"] == "done"
    assert result_msg.payload["result"]["context_pointer"] == "indiehackers_summary.txt"
