import abc
import logging
from typing import List, Dict, Any, Type, Optional, TypeVar, Union
from pydantic import BaseModel
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from aegisos.core.config import CONFIG

# 配置日志
logger = logging.getLogger("LLMEngine")

T = TypeVar("T", bound=BaseModel)

class BaseLLMEngine(abc.ABC):
    """
    LLM 引擎抽象基类
    """
    @abc.abstractmethod
    async def generate(
        self, 
        messages: List[Dict[str, str]], 
        response_model: Optional[Type[T]] = None,
        **kwargs
    ) -> Union[str, T]:
        """
        生成文本或结构化对象。
        """
        pass

class OpenAIEngine(BaseLLMEngine):
    """
    OpenAI 引擎实现 (支持 GPT-4, GPT-3.5 以及所有兼容 OpenAI 格式的后端)
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
                # 使用 OpenAI 的 Structured Outputs 功能
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
    Anthropic 引擎实现 (Claude 3.x 系列)
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
            # Anthropic 目前原生不支持像 OpenAI 那样的 Pydantic 直接解析
            # 这里我们通过提示词强制并手动解析（或者使用工具调用来实现结构化输出）
            # 为了简洁，目前先实现基础的文本生成，结构化建议通过 Tool Use 实现
            system_msg = ""
            user_msgs = []
            for m in messages:
                if m["role"] == "system":
                    system_msg = m["content"]
                else:
                    user_msgs.append({"role": m["role"], "content": m["content"]})

            if response_model:
                # 简单实现：通过提示词强制 JSON 并解析
                # 在真实生产中，更推荐使用 tool_use (Beta)
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
