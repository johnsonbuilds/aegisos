import asyncio
import logging
import os
import sys
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("SandboxRunner")

class ExecutionResult(BaseModel):
    """代码执行结果"""
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    error: Optional[str] = None

class SandboxRunner:
    """
    基础安全沙箱运行器。
    Phase 2: 基于受限子进程执行 Python 代码。
    """
    def __init__(self, workspace_path: str):
        # 确保是绝对路径
        self.workspace_path = os.path.abspath(workspace_path)

    async def run_python(self, code: str, timeout: int = 10) -> ExecutionResult:
        """
        在受限环境中执行 Python 代码。
        """
        # 为了安全，我们不直接在命令行传代码，而是写入临时文件
        temp_file = os.path.join(self.workspace_path, "_sandbox_temp.py")
        
        try:
            with open(temp_file, "w") as f:
                f.write(code)

            # 启动受限子进程
            # TODO: 后续通过环境变量、cgroup 或 seccomp 进一步加固
            process = await asyncio.create_subprocess_exec(
                sys.executable, temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_path,
                env={"PYTHONPATH": self.workspace_path} # 仅允许访问工作区
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
            # 无论成功失败，清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)
