import re
from enum import Enum
from typing import Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator

class AACPIntent(str, Enum):
    # Basic intents
    REQUEST = "REQUEST"
    PROPOSE = "PROPOSE"
    INFORM = "INFORM"
    TASK_COMPLETE = "TASK_COMPLETE"
    ERROR = "ERROR"
    
    # System-level intents
    SPAWN = "SPAWN"          # Create/Spawn Agent
    TERMINATE = "TERMINATE"  # Destroy/Terminate Agent

# Agent URI specification: {role}_{uuid}@{instance} or {role}@{instance}
AGENT_URI_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+(@[a-zA-Z0-9_\-]+)?$")

def parse_agent_uri(uri: str) -> Tuple[str, str, Optional[str]]:
    """
    Parse an Agent URI into (role, instance, uuid).
    Returns (role, instance, uid_str)
    """
    if uri == "BROADCAST":
        return "BROADCAST", "all", None
        
    if "@" in uri:
        full_id, instance = uri.split("@", 1)
    else:
        full_id, instance = uri, "local"

    if "_" in full_id:
        parts = full_id.rsplit("_", 1)
        role, uid = parts[0], parts[1]
    else:
        role, uid = full_id, None
        
    return role, instance, uid

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
            raise ValueError(f"Invalid Agent URI format: '{v}'. Use '{{role}}_{{uuid}}@{{instance}}' or '{{role}}@{{instance}}'")
        # Ensure it has an instance part if not provided
        if "@" not in v:
            return f"{v}@local"
        return v
