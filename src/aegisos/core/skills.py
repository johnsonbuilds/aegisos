import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel

logger = logging.getLogger("AegisSkill")

class SkillResult(BaseModel):
    """Result of a skill execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None

class BaseSkill(ABC):
    """
    Base class for all AegisOS Skills.
    Skills are pluggable modules that extend Agent capabilities.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def execute(self, payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> SkillResult:
        """
        Execute the skill logic.
        :param payload: Parameters for the skill (usually from AACPMessage.payload)
        :param context: Optional context (e.g., workspace_path, agent_id)
        """
        pass

    def check_dependencies(self) -> bool:
        """
        Check if required third-party libraries are installed.
        Default returns True. Override if needed.
        """
        return True
