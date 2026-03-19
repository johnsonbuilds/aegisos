import pytest
import json
import asyncio
from unittest.mock import MagicMock, AsyncMock
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.agents.base import AACPAgent, AACPResponse
from aegisos.core.llm import BaseLLMEngine
from aegisos.core.workspace import WorkspaceManager
from aegisos.agents.common import CoordinatorAgent
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
