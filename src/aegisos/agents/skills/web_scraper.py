import httpx
import re
import os
import uuid
import logging
from typing import Any, Dict, Optional
from aegisos.core.skills import BaseSkill, SkillResult
from aegisos.core.actions import AACPAction

logger = logging.getLogger("WebScraperSkill")

class WebScraperSkill(BaseSkill):
    """
    Skill for fetching web pages and saving them to the workspace.
    """
    def __init__(self):
        super().__init__(name=AACPAction.WEB_FETCH.value)

    async def execute(self, payload: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> SkillResult:
        url = payload.get("url")
        mode = payload.get("mode", "markdown")
        timeout = payload.get("timeout", 10)
        workspace_path = context.get("workspace_path") if context else None

        if not url:
            return SkillResult(success=False, error="URL is required")
        if not workspace_path:
            return SkillResult(success=False, error="Workspace path is required for persistent storage")

        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                
                content = response.text
                processed_content = self._simple_html_to_md(content) if mode == "markdown" else content

                # --- Persistence Strategy (Architecture #5.2) ---
                # Save to _workspace/downloads/
                download_dir = os.path.join(workspace_path, "downloads")
                os.makedirs(download_dir, exist_ok=True)
                
                filename = f"web_{uuid.uuid4().hex[:8]}.md"
                file_path = os.path.join("downloads", filename)
                full_path = os.path.join(workspace_path, file_path)
                
                with open(full_path, "w") as f:
                    f.write(processed_content)

                logger.info(f"Web content saved to {file_path}")

                return SkillResult(
                    success=True, 
                    data={
                        "url": url,
                        "status_code": response.status_code,
                        "context_pointer": file_path, # Return file path
                        "message": f"Content saved to {file_path}"
                    }
                )

        except Exception as e:
            logger.error(f"WebScraperSkill error: {e}")
            return SkillResult(success=False, error=str(e))

    def _simple_html_to_md(self, html: str) -> str:
        """A very primitive HTML to Markdown converter to avoid heavy dependencies."""
        # 1. Strip script and style tags
        html = re.sub(r'<(script|style|nav|footer)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
        
        # 2. H1-H3 to #
        html = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n# \1\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1\n', html, flags=re.IGNORECASE)
        html = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1\n', html, flags=re.IGNORECASE)
        
        # 3. Links [text](url)
        html = re.sub(r'<a[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', r'[\2](\1)', html, flags=re.IGNORECASE)
        
        # 4. Strip all other tags
        text = self._strip_tags(html)
        
        # 5. Collapse multiple newlines
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()

    def _strip_tags(self, html: str) -> str:
        return re.sub(r'<[^>]*>', '', html).strip()
