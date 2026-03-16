import logging
from typing import Dict, Type, Any, Optional

logger = logging.getLogger("AgentFactory")

class AgentFactory:
    """
    负责 Agent 类的注册与实例化逻辑。
    将具体的 Agent 实现与 Dispatcher 内核解耦。
    """
    _registry: Dict[str, Type] = {}

    @classmethod
    def register(cls, agent_type: str, agent_class: Type):
        """注册一个新的 Agent 类型"""
        cls._registry[agent_type] = agent_class
        logger.info(f"Agent type '{agent_type}' registered with class {agent_class.__name__}")

    @classmethod
    def create(cls, agent_type: str, **kwargs) -> Any:
        """根据类型实例化 Agent"""
        if agent_type not in cls._registry:
            # 尝试延迟加载默认类型以避免循环引用
            cls._lazy_load_defaults()
            
        if agent_type not in cls._registry:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        agent_class = cls._registry[agent_type]
        logger.debug(f"Instantiating {agent_type} agent...")
        return agent_class(**kwargs)

    @classmethod
    def _lazy_load_defaults(cls):
        """按需加载内置 Agent 类型"""
        try:
            from aegisos.agents.base import AACPAgent
            cls.register("llm", AACPAgent)
        except ImportError:
            logger.warning("Could not lazy load AACPAgent")
            
        try:
            from aegisos.agents.stub import StubAgent
            cls.register("stub", StubAgent)
        except ImportError:
            logger.warning("Could not lazy load StubAgent")

# 全局单例
AGENT_FACTORY = AgentFactory
