import os
import logging
from typing import Any, Dict, Optional
from aegisos.core.skills import BaseSkill, SkillResult
from aegisos.core.actions import AACPAction

logger = logging.getLogger("FileSystemSkill")

class FileSystemSkill(BaseSkill):
    """
    Skill for basic file system operations.
    """
    def __init__(self, name: str):
        super().__init__(name=name)

    async def execute(self, payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> SkillResult:
        workspace_path = context.get("workspace_path") if context else None
        if not workspace_path:
            return SkillResult(success=False, error="Workspace path is required")

        path = payload.get("path")
        if not path:
            return SkillResult(success=False, error="File path is required")
            
        full_path = os.path.join(workspace_path, path)
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            if self.name == AACPAction.FILE_WRITE.value:
                content = payload.get("content", "")
                with open(full_path, "w") as f:
                    f.write(content)
                return SkillResult(success=True, data={"path": path, "message": f"File written to {path}"})
            
            elif self.name == AACPAction.FILE_READ.value:
                if not os.path.exists(full_path):
                    return SkillResult(success=False, error=f"File not found: {path}")
                with open(full_path, "r") as f:
                    content = f.read()
                return SkillResult(success=True, data={"path": path, "content": content})
            
            return SkillResult(success=False, error=f"Unsupported action: {self.name}")

        except Exception as e:
            logger.error(f"FileSystemSkill error: {e}")
            return SkillResult(success=False, error=str(e))
