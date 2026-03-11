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
        # 确保 base_dir 和 session_id 的组合路径是绝对路径，方便后续校验
        self.root_path = Path(base_dir).resolve() / session_id
        self.root_path.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, path_str: str) -> Path:
        """
        验证并返回安全的路径。
        防止路径穿越攻击（Path Traversal）。
        """
        target_path = (self.root_path / path_str).resolve()
        # 检查 target_path 是否位于 root_path 目录下
        if not target_path.is_relative_to(self.root_path):
            raise PermissionError(f"Access denied: {path_str} is outside the workspace.")
        return target_path

    async def write_file(self, filename: str, content: str) -> str:
        """异步写入文件"""
        target_path = self._safe_path(filename)
        # 确保父目录存在（支持子目录写入）
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(target_path, mode='w', encoding='utf-8') as f:
            await f.write(content)
        
        # 返回相对于根目录的相对路径字符串
        return str(target_path.relative_to(self.root_path))

    async def read_file(self, filepath: str) -> str:
        """异步读取文件"""
        target_path = self._safe_path(filepath)
        if not target_path.is_file():
            raise FileNotFoundError(f"File not found: {filepath}")
            
        async with aiofiles.open(target_path, mode='r', encoding='utf-8') as f:
            return await f.read()

    async def list_files(self, sub_dir: str = ".") -> List[str]:
        """列出工作区内的所有文件（相对于根目录）"""
        target_dir = self._safe_path(sub_dir)
        files = []
        for file_path in target_dir.rglob("*"):
            if file_path.is_file():
                # 返回相对于根目录的路径
                files.append(str(file_path.relative_to(self.root_path)))
        return files
