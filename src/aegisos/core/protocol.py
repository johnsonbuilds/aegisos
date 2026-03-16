import re
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

class AACPIntent(str, Enum):
    # 基础意图
    REQUEST = "REQUEST"
    PROPOSE = "PROPOSE"
    INFORM = "INFORM"
    TASK_COMPLETE = "TASK_COMPLETE"
    ERROR = "ERROR"
    
    # 系统级意图
    SPAWN = "SPAWN"          # 创建/孵化 Agent
    TERMINATE = "TERMINATE"  # 销毁/终止 Agent

# Agent URI 规范: {id}@{instance}
AGENT_URI_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+@[a-zA-Z0-9_\-]+$")

class AACPMessage(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    message_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.now)
    sender: str
    receiver: str
    intent: AACPIntent
    payload: Dict[str, Any] = Field(default_factory=dict)
    context_pointer: Optional[str] = None

    @field_validator("sender", "receiver")
    @classmethod
    def validate_agent_uri(cls, v: str) -> str:
        if v == "BROADCAST":
            return v
        if not AGENT_URI_PATTERN.match(v):
            raise ValueError(f"Invalid Agent URI format: '{v}'. Must be '{{id}}@{{instance}}'")
        return v
