from enum import Enum
from typing import Dict, Any, Type, Optional
from pydantic import BaseModel, Field

class AACPAction(str, Enum):
    """
    AegisOS 标准动作集。
    这些动作通常作为 REQUEST 意图的 payload["action"] 字段。
    """
    # 执行类 (Execution)
    CODE_EXEC = "core.exec.code"        # 执行代码 (通用)
    PYTHON_RUN = "core.exec.python"    # 运行 Python 脚本
    
    # 存储类 (Storage)
    FILE_READ = "core.fs.read"         # 读取文件
    FILE_WRITE = "core.fs.write"       # 写入文件
    
    # 认知类 (Cognition)
    WEB_SEARCH = "core.cog.web_search" # 网页搜索
    MEM_RETRIEVE = "core.cog.mem_get"  # 检索长期记忆

class ActionPayload(BaseModel):
    """所有 Action Payload 的基类"""
    pass

class CodeExecPayload(ActionPayload):
    """core.exec.code 的参数规范"""
    language: str = Field(..., description="编程语言，如 'python', 'bash'")
    code: str = Field(..., description="待执行的源代码")
    timeout: int = Field(10, description="执行超时时间(秒)")

# 动作到 Payload 模型映射 (用于自动校验)
ACTION_SCHEMAS: Dict[AACPAction, Type[ActionPayload]] = {
    AACPAction.CODE_EXEC: CodeExecPayload,
    AACPAction.PYTHON_RUN: CodeExecPayload, # 复用
}
