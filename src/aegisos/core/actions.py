from enum import Enum
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel, Field

class AACPAction(str, Enum):
    """
    AegisOS standard action set.
    These actions are typically used as the payload["action"] field for REQUEST intent.
    """
    # Execution
    CODE_EXEC = "core.exec.code"        # Execute code (general)
    PYTHON_RUN = "core.exec.python"    # Run Python script
    
    # Storage
    FILE_READ = "core.fs.read"         # Read file
    FILE_WRITE = "core.fs.write"       # Write file
    
    # Cognition
    WEB_SEARCH = "core.cog.web_search" # Web search
    MEM_RETRIEVE = "core.cog.mem_get"  # Retrieve long-term memory

class ActionPayload(BaseModel):
    """Base class for all Action Payloads."""
    pass

class CodeExecPayload(ActionPayload):
    """Parameter specification for core.exec.code."""
    language: str = Field(..., description="Programming language, such as 'python', 'bash'")
    code: str = Field(..., description="Source code to be executed")
    timeout: int = Field(10, description="Execution timeout (seconds)")

# Action to Payload model mapping (for automatic validation)
ACTION_SCHEMAS: Dict[AACPAction, Type[ActionPayload]] = {
    AACPAction.CODE_EXEC: CodeExecPayload,
    AACPAction.PYTHON_RUN: CodeExecPayload, # Reuse
}
