import pytest
from unittest.mock import AsyncMock, patch
from pydantic import BaseModel
from aegisos.core.llm import OpenAIEngine, AnthropicEngine

class SimpleResponse(BaseModel):
    answer: str
    confidence: float

@pytest.mark.asyncio
async def test_openai_engine_structured():
    engine = OpenAIEngine(api_key="fake-key")
    
    mock_response = AsyncMock()
    # 模拟 OpenAI beta.chat.completions.parse 的返回结构
    mock_response.choices = [
        AsyncMock(message=AsyncMock(parsed=SimpleResponse(answer="hello", confidence=0.99)))
    ]
    
    with patch.object(engine.client.beta.chat.completions, 'parse', new_callable=AsyncMock) as mock_parse:
        mock_parse.return_value = mock_response
        messages = [{"role": "user", "content": "hi"}]
        result = await engine.generate(messages, response_model=SimpleResponse)
        
        assert isinstance(result, SimpleResponse)
        assert result.answer == "hello"
        assert result.confidence == 0.99

@pytest.mark.asyncio
async def test_anthropic_engine_text():
    engine = AnthropicEngine(api_key="fake-key")
    
    mock_response = AsyncMock()
    # Anthropic response content is a list of blocks
    mock_content_block = AsyncMock()
    mock_content_block.text = "I am Claude"
    mock_response.content = [mock_content_block]
    
    with patch.object(engine.client.messages, 'create', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        messages = [{"role": "user", "content": "who are you?"}]
        result = await engine.generate(messages)
        
        assert result == "I am Claude"
