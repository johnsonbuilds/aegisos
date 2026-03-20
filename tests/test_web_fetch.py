import pytest
import asyncio
import os
from unittest.mock import AsyncMock, patch, MagicMock
from aegisos.agents.skills.web_fetch import WebFetchSkill, FetchResult, SimpleHttpEngine, ENGINE_REGISTRY
from aegisos.core.actions import AACPAction
from aegisos.agents.base import AACPAgent, AACPResponse
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.config import CONFIG

@pytest.fixture
def mock_workspace(tmp_path):
    workspace = MagicMock()
    workspace.root_path = tmp_path
    return workspace

@pytest.mark.asyncio
async def test_simple_http_engine_success():
    engine = SimpleHttpEngine()
    url = "https://example.com"
    
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html><body><h1>Hello</h1></body></html>"
        mock_get.return_value = mock_resp
        
        result = await engine.fetch(url)
        
        assert result.url == url
        assert result.status_code == 200
        assert "Hello" in result.content
        assert result.error is None

@pytest.mark.asyncio
async def test_web_fetch_skill_persistence(mock_workspace):
    skill = WebFetchSkill()
    url = "https://example.com"
    payload = {"url": url, "mode": "markdown"}
    context = {
        "workspace_path": str(mock_workspace.root_path),
        "agent_id": "test_agent@local"
    }
    
    with patch.dict(ENGINE_REGISTRY, {"simple": AsyncMock(spec=SimpleHttpEngine)}):
        mock_engine = ENGINE_REGISTRY["simple"]
        mock_engine.fetch.return_value = FetchResult(
            url=url,
            status_code=200,
            content="<html><body><h1>Hello World</h1></body></html>",
            metadata={}
        )
        
        result = await skill.execute(payload, context)
        
        assert result.success is True
        assert "context_pointer" in result.data
        
        # Verify persistence
        file_path = result.data["context_pointer"]
        full_path = os.path.join(str(mock_workspace.root_path), file_path)
        assert os.path.exists(full_path)
        
        with open(full_path, "r") as f:
            content = f.read()
            assert "# Hello World" in content # Markdown conversion check

@pytest.mark.asyncio
async def test_web_fetch_skill_error_handling(mock_workspace):
    skill = WebFetchSkill()
    payload = {"url": "https://error.com"}
    context = {"workspace_path": str(mock_workspace.root_path)}
    
    with patch.dict(ENGINE_REGISTRY, {"simple": AsyncMock(spec=SimpleHttpEngine)}):
        mock_engine = ENGINE_REGISTRY["simple"]
        mock_engine.fetch.return_value = FetchResult(
            url="https://error.com",
            status_code=404,
            content="",
            metadata={},
            error="HTTP Error 404"
        )
        
        result = await skill.execute(payload, context)
        
        assert result.success is False
        assert "404" in result.error

@pytest.mark.asyncio
async def test_worker_agent_injection():
    from aegisos.agents.common import WorkerAgent
    mock_llm = AsyncMock()
    
    worker = WorkerAgent(llm_engine=mock_llm)
    
    # Verify the new skill is registered
    assert AACPAction.WEB_FETCH.value in worker.skills
    assert isinstance(worker.skills[AACPAction.WEB_FETCH.value], WebFetchSkill)
