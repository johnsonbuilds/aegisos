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

    def get_description(self) -> str:
        """Return a concise human-readable description for prompt injection."""
        return (self.__doc__ or "").strip() or "No description available."

    def get_input_schema(self) -> Dict[str, Any]:
        """Return a model-agnostic input schema for this skill."""
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        }

    def describe(self) -> Dict[str, Any]:
        """Return structured metadata about the skill."""
        return {
            "name": self.name,
            "description": self.get_description(),
            "input_schema": self.get_input_schema(),
        }

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
