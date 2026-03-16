import os
import aiofiles
from pathlib import Path
from typing import Optional, List
from uuid import uuid4

class WorkspaceManager:
    def __init__(self, base_dir: str = "_workspace", session_id: Optional[str] = None):
        if session_id is None:
            session_id = str(uuid4())
        
        self.session_id = session_id
        # Ensure the combination of base_dir and session_id is an absolute path for easier validation
        self.root_path = Path(base_dir).resolve() / session_id
        self.root_path.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, path_str: str) -> Path:
        """
        Validate and return a safe path.
        Prevent path traversal attacks.
        """
        target_path = (self.root_path / path_str).resolve()
        # Check if target_path is within the root_path directory
        if not target_path.is_relative_to(self.root_path):
            raise PermissionError(f"Access denied: {path_str} is outside the workspace.")
        return target_path

    async def write_file(self, filename: str, content: str) -> str:
        """Asynchronously write a file."""
        target_path = self._safe_path(filename)
        # Ensure the parent directory exists (supports writing to subdirectories)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(target_path, mode='w', encoding='utf-8') as f:
            await f.write(content)
        
        # Return the relative path string relative to the root directory
        return str(target_path.relative_to(self.root_path))

    async def read_file(self, filepath: str) -> str:
        """Asynchronously read a file."""
        target_path = self._safe_path(filepath)
        if not target_path.is_file():
            raise FileNotFoundError(f"File not found: {filepath}")
            
        async with aiofiles.open(target_path, mode='r', encoding='utf-8') as f:
            return await f.read()

    async def list_files(self, sub_dir: str = ".") -> List[str]:
        """List all files in the workspace (relative to the root directory)."""
        target_dir = self._safe_path(sub_dir)
        files = []
        for file_path in target_dir.rglob("*"):
            if file_path.is_file():
                # Return the path relative to the root directory
                files.append(str(file_path.relative_to(self.root_path)))
        return files
