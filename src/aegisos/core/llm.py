import abc
import logging
from typing import List, Dict, Any, Type, Optional, TypeVar, Union
from pydantic import BaseModel
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from aegisos.core.config import CONFIG

# Configure logging
logger = logging.getLogger("LLMEngine")

T = TypeVar("T", bound=BaseModel)

class BaseLLMEngine(abc.ABC):
    """
    Abstract base class for LLM engines
    """
    @abc.abstractmethod
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        response_model: Optional[Type[T]] = None,
        **kwargs
    ) -> Union[str, T]:
        """
        Generate text or structured objects.
        """
        pass

class OpenAIEngine(BaseLLMEngine):
    """
    OpenAI engine implementation (supports GPT-4, GPT-3.5, and all OpenAI-compatible backends)
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.client = AsyncOpenAI(
            api_key=api_key or CONFIG.openai_api_key,
            base_url=base_url or CONFIG.openai_base_url
        )
        self.model = model or CONFIG.openai_model

    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        response_model: Optional[Type[T]] = None,
        **kwargs
    ) -> Union[str, T]:
        try:
            if response_model:
                # Use OpenAI's Structured Outputs feature
                completion = await self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=messages,
                    response_format=response_model,
                    **kwargs
                )
                return completion.choices[0].message.parsed
            else:
                completion = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **kwargs
                )
                return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI Generation Error: {e}", exc_info=True)
            raise

class AnthropicEngine(BaseLLMEngine):
    """
    Anthropic engine implementation (Claude 3.x series)
    """
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.client = AsyncAnthropic(api_key=api_key or CONFIG.anthropic_api_key)
        self.model = model or CONFIG.anthropic_model

    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        response_model: Optional[Type[T]] = None,
        **kwargs
    ) -> Union[str, T]:
        try:
            # Anthropic currently does not natively support direct Pydantic parsing like OpenAI
            # Here we force and manually parse via prompting (or use tool use for structured output)
            # For simplicity, basic text generation is implemented; structured output is recommended via Tool Use
            system_msg = ""
            user_msgs = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    user_msgs.append({"role": m["role"], "content": m["content"]})

            if response_model:
                # Simple implementation: force JSON and parse via prompting
                # In production, tool_use (Beta) is recommended
                logger.warning("Anthropic structured output is currently emulated via prompt forcing.")
                prompt_suffix = f"\n\nIMPORTANT: You must return ONLY a valid JSON object matching this schema: {response_model.model_json_schema()}"
                user_msgs[-1]["content"] += prompt_suffix
                
                response = await self.client.messages.create(
                    model=self.model,
                    system=system_msg,
                    messages=user_msgs,
                    max_tokens=4096,
                    **kwargs
                )
                content = response.content[0].text
                return response_model.model_validate_json(content)
            else:
                response = await self.client.messages.create(
                    model=self.model,
                    system=system_msg,
                    messages=user_msgs,
                    max_tokens=4096,
                    **kwargs
                )
                return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic Generation Error: {e}", exc_info=True)
            raise
