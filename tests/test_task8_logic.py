import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch
from aegisos.agents.base import AACPAgent, AACPResponse
from aegisos.agents.skills.web_scraper import WebScraperSkill
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.actions import AACPAction
from aegisos.core.skills import SkillResult

@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    return llm

@pytest.fixture
def agent(mock_llm):
    return AACPAgent(
        role="worker",
        llm_engine=mock_llm,
        system_prompt="Test Prompt"
    )

@pytest.mark.asyncio
async def test_web_scraper_skill(tmp_path):
    skill = WebScraperSkill()
    workspace_path = str(tmp_path)
    
    # Mock httpx response
    mock_response = AsyncMock()
    mock_response.text = "<html><body><h1>Title</h1><p>Content</p></body></html>"
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None

    with patch("httpx.AsyncClient.get", return_value=mock_response):
        payload = {"url": "https://example.com", "mode": "markdown"}
        # Provide workspace_path in context
        result = await skill.execute(payload, context={"workspace_path": workspace_path})
        
        assert result.success is True
        assert "context_pointer" in result.data
        
        # Verify file exists
        file_path = os.path.join(workspace_path, result.data["context_pointer"])
        assert os.path.exists(file_path)
        with open(file_path, "r") as f:
            content = f.read()
            assert "# Title" in content

@pytest.mark.asyncio
async def test_agent_skill_execution(agent, mock_llm, tmp_path):
    # Register skill to agent
    skill = WebScraperSkill()
    agent.add_skill(skill)
    agent.workspace = AsyncMock()
    agent.workspace.root_path = tmp_path
    
    # Mock LLM to return a self-request
    mock_llm.generate.side_effect = [
        AACPResponse(
            thought="Fetch URL",
            receiver=agent.agent_id,
            intent=AACPIntent.REQUEST,
            action=AACPAction.WEB_FETCH,
            payload={"url": "https://example.com"}
        ),
        AACPResponse(
            thought="Done",
            receiver="user",
            intent=AACPIntent.INFORM,
            payload={"done": True}
        )
    ]

    # Mock Skill execution
    with patch.object(WebScraperSkill, "execute", return_value=SkillResult(success=True, data={"context_pointer": "downloads/web_abc.md"})):
        await agent.think()
        
        # Verify result feedback contains context_pointer
        history = agent.memory.get_context()
        assert any("downloads/web_abc.md" in m["content"] for m in history)
