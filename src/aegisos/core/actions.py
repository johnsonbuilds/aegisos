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
    WEB_FETCH = "core.cog.web_fetch"   # Fetch webpage (raw/markdown)
    WEB_PARSE = "core.cog.web_parse"   # Parse webpage (structured)
    MEM_RETRIEVE = "core.cog.mem_get"  # Retrieve long-term memory

class ActionPayload(BaseModel):
    """Base class for all Action Payloads."""
    pass

class CodeExecPayload(ActionPayload):
    """Parameter specification for core.exec.code."""
    language: str = Field(..., description="Programming language, such as 'python', 'bash'")
    code: str = Field(..., description="Source code to be executed")
    timeout: int = Field(10, description="Execution timeout (seconds)")

class WebFetchPayload(ActionPayload):
    """Parameter specification for core.cog.web_fetch."""
    url: str = Field(..., description="URL to fetch")
    mode: str = Field("markdown", description="Output mode: 'raw', 'markdown', 'text'")
    engine: str = Field("simple", description="Engine to use: 'simple'")

# Action to Payload model mapping (for automatic validation)
ACTION_SCHEMAS: Dict[AACPAction, Type[ActionPayload]] = {
    AACPAction.CODE_EXEC: CodeExecPayload,
    AACPAction.PYTHON_RUN: CodeExecPayload, # Reuse
    AACPAction.WEB_FETCH: WebFetchPayload,
}
