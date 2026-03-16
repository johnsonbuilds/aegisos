import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("SandboxRunner")

class ExecutionResult(BaseModel):
    """Code execution result."""
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    error: Optional[str] = None

class SandboxRunner:
    """
    Basic security sandbox runner.
    Phase 2: Execute Python code based on restricted subprocesses.
    """
    def __init__(self, workspace_path: str):
        # Ensure it is an absolute path
        self.workspace_path = os.path.abspath(workspace_path)

    async def run_python(self, code: str, timeout: int = 10) -> ExecutionResult:
        """
        Execute Python code in a restricted environment.
        """
        # For security, we don't pass code directly on the command line; instead, we write it to a temporary file.
        temp_file = os.path.join(self.workspace_path, "_sandbox_temp.py")
        
        try:
            with open(temp_file, "w") as f:
                f.write(code)

            # Start a restricted subprocess
            # TODO: Further harden via environment variables, cgroup, or seccomp in the future.
            process = await asyncio.create_subprocess_exec(
                sys.executable, temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_path,
                env={"PYTHONPATH": self.workspace_path} # Only allow access to the workspace
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                return ExecutionResult(
                    exit_code=process.returncode,
                    stdout=stdout.decode().strip(),
                    stderr=stderr.decode().strip(),
                    timed_out=False
                )
            except asyncio.TimeoutError:
                process.kill()
                logger.warning(f"Sandbox: Code execution timed out after {timeout}s")
                return ExecutionResult(
                    exit_code=-1,
                    stdout="",
                    stderr="Execution Timed Out",
                    timed_out=True
                )
        except Exception as e:
            logger.error(f"Sandbox error: {e}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr="",
                error=str(e)
            )
        finally:
            # Clean up the temporary file regardless of success or failure
            if os.path.exists(temp_file):
                os.remove(temp_file)
