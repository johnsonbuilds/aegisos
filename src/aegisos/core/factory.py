import logging
from typing import Dict, Type, Any, Optional

logger = logging.getLogger("AgentFactory")

class AgentFactory:
    """
    Responsible for Agent class registration and instantiation logic.
    Decouples specific Agent implementations from the Dispatcher core.
    """
    _registry: Dict[str, Type] = {}

    @classmethod
    def register(cls, agent_type: str, agent_class: Type):
        """Register a new Agent type"""
        cls._registry[agent_type] = agent_class
        logger.info(f"Agent type '{agent_type}' registered with class {agent_class.__name__}")

    @classmethod
    def create(cls, agent_type: str, **kwargs) -> Any:
        """Instantiate an Agent based on its type"""
        if agent_type not in cls._registry:
            # Attempt lazy loading of default types to avoid circular imports
            cls._lazy_load_defaults()
            
        if agent_type not in cls._registry:
            raise ValueError(f"Unknown agent type: {agent_type}")
            
        agent_class = cls._registry[agent_type]
        logger.debug(f"Instantiating {agent_type} agent...")
        return agent_class(**kwargs)

    @classmethod
    def _lazy_load_defaults(cls):
        """Load built-in Agent types on demand"""
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

# Global singleton
AGENT_FACTORY = AgentFactory
