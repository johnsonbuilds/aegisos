from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class AACPIntent(str, Enum):
    REQUEST = "REQUEST"
    PROPOSE = "PROPOSE"
    INFORM = "INFORM"
    TASK_COMPLETE = "TASK_COMPLETE"
    ERROR = "ERROR"

class AACPMessage(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    
    message_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.now)
    sender: str
    receiver: str
    intent: AACPIntent
    payload: Dict[str, Any] = Field(default_factory=dict)
    context_pointer: Optional[str] = None
