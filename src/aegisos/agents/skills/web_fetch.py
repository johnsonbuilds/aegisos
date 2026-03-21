import logging
import httpx
import re
import os
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel
from aegisos.core.skills import BaseSkill, SkillResult
from aegisos.core.actions import AACPAction

logger = logging.getLogger("WebFetchSkill")

# --- 1. FetchResult Schema (Internal Engine Response) ---
class FetchResult(BaseModel):
    url: str
    status_code: int
    content: str
    metadata: Dict[str, Any]
    error: Optional[str] = None

# --- 2. Engine Interface ---
class BaseFetchEngine(ABC):
    @abstractmethod
    async def fetch(self, url: str, **kwargs) -> FetchResult:
        pass

# --- 3. SimpleHttpEngine (MVP) ---
class SimpleHttpEngine(BaseFetchEngine):
    async def fetch(self, url: str, **kwargs) -> FetchResult:
        timeout = kwargs.get("timeout", 10)
        headers = kwargs.get("headers", {})
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
                resp = await client.get(url)
                return FetchResult(
                    url=url,
                    status_code=resp.status_code,
                    content=resp.text,
                    metadata={},
                    error=None if resp.status_code < 400 else f"HTTP Error {resp.status_code}"
                )
        except Exception as e:
            return FetchResult(
                url=url,
                status_code=0,
                content="",
                metadata={},
                error=str(e)
            )

# --- 4. Engine Registry ---
ENGINE_REGISTRY: Dict[str, BaseFetchEngine] = {
    "simple": SimpleHttpEngine(),
    "default": SimpleHttpEngine(),
}

# --- 5. WebFetchSkill ---
class WebFetchSkill(BaseSkill):
    """
    Unified Web Fetch Skill with Workspace persistence.
    Args:
        url (str): The URL to fetch.
        mode (str, optional): 'markdown' (default) or 'html'.
        engine (str, optional): 'simple' (default).
    """
    def __init__(self):
        super().__init__(name=AACPAction.WEB_FETCH.value)

    def get_description(self) -> str:
        return "Fetch a web page and persist the result into the workspace, returning a context pointer."

    def get_input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Absolute URL to fetch.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["markdown", "html"],
                    "description": "Persist output as Markdown or raw HTML.",
                },
                "engine": {
                    "type": "string",
                    "description": "Fetcher implementation name. Unknown values fall back to the default engine.",
                },
                "timeout": {
                    "type": "number",
                    "description": "Optional request timeout in seconds.",
                },
                "headers": {
                    "type": "object",
                    "description": "Optional HTTP headers map.",
                    "additionalProperties": {"type": "string"},
                },
            },
            "required": ["url"],
            "additionalProperties": True,
        }

    async def execute(self, payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> SkillResult:
        url = payload.get("url")
        mode = payload.get("mode", "markdown")
        engine_name = payload.get("engine", "simple")
        workspace_path = context.get("workspace_path") if context else None
        
        if not url:
            return SkillResult(success=False, error="URL is required")
        if not workspace_path:
            return SkillResult(success=False, error="Workspace path is required for persistence")
            
        engine = ENGINE_REGISTRY.get(engine_name)
        if not engine:
            logger.warning(f"Unknown engine: {engine_name}. Defaulting to 'simple'.")
            engine = ENGINE_REGISTRY.get("simple")
            
        # 1. Engine Fetch
        fetch_kwargs = payload.copy()
        if "url" in fetch_kwargs:
            del fetch_kwargs["url"]
            
        result = await engine.fetch(url, **fetch_kwargs)
        
        if result.error:
            return SkillResult(success=False, error=result.error)
            
        # 2. Content Processing (HTML to Markdown)
        content = result.content
        if mode == "markdown":
            content = self._simple_html_to_md(content)

        # 3. Persistence to Workspace (AegisOS Principle: Large data stays in workspace)
        try:
            download_dir = os.path.join(workspace_path, "downloads")
            os.makedirs(download_dir, exist_ok=True)
            
            agent_id = context.get("agent_id", "agent").split("@")[0]
            extension = ".md" if mode == "markdown" else ".html"
            filename = f"{agent_id}_{uuid.uuid4().hex[:6]}{extension}"
            file_path = os.path.join("downloads", filename)
            full_path = os.path.join(workspace_path, file_path)
            
            with open(full_path, "w") as f:
                f.write(content)

            logger.info(f"Web content saved to {file_path}")

            # 4. Return lightweight context pointer
            return SkillResult(
                success=True,
                data={
                    "url": url,
                    "status_code": result.status_code,
                    "context_pointer": file_path,
                    "message": f"Successfully fetched and saved to {file_path}"
                }
            )
        except Exception as e:
            return SkillResult(success=False, error=f"Persistence error: {str(e)}")

    def _simple_html_to_md(self, html: str) -> str:
        """A primitive HTML to Markdown converter."""
        # Strip script and style tags
        html = re.sub(r'<(script|style|nav|footer)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # H1-H3 to #
        html = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', html, flags=re.IGNORECASE)
        # Links [text](url)
        html = re.sub(r'<a[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', r'[\2](\1)', html, flags=re.IGNORECASE)
        # Strip all other tags
        text = re.sub(r'<[^>]*>', '', html).strip()
        # Collapse multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
