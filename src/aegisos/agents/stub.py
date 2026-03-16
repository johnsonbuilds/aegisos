import logging
import uuid
from typing import Optional, Any
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.config import CONFIG

logger = logging.getLogger("StubAgent")

class StubAgent:
    """
    用于测试和逻辑验证的非 LLM 代理。
    它不依赖 LLM 引擎，仅执行简单的固定逻辑或透传。
    """
    def __init__(
        self, 
        role: str = "stub", 
        agent_id: Optional[str] = None,
        dispatcher: Optional[Any] = None,
        **kwargs
    ):
        if not agent_id:
            uid = str(uuid.uuid4())[:8]
            self.agent_id = f"{role}_{uid}@{CONFIG.instance_id}"
        else:
            self.agent_id = agent_id if "@" in agent_id else f"{agent_id}@{CONFIG.instance_id}"

        self.role = role
        self.dispatcher = dispatcher
        logger.info(f"StubAgent {self.agent_id} initialized.")

    async def handle_message(self, message: AACPMessage):
        """
        StubAgent 的核心逻辑：仅记录日志。
        具体的业务模拟通常在测试脚本中通过 Monkeypatch 或子类化来实现。
        """
        logger.info(f"[StubAgent:{self.agent_id}] Received: {message.intent} from {message.sender}")
        # 默认不做任何回复，除非在子类中覆盖
