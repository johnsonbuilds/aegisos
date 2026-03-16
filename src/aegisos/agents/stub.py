import logging
import uuid
from typing import Optional, Any
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.config import CONFIG

logger = logging.getLogger("StubAgent")

class StubAgent:
    """
    Non-LLM agent used for testing and logic verification.
    It does not rely on an LLM engine, only executing simple fixed logic or pass-through.
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
        Core logic of StubAgent: only log records.
        Specific business simulations are usually implemented in test scripts via Monkeypatch or subclassing.
        """
        logger.info(f"[StubAgent:{self.agent_id}] Received: {message.intent} from {message.sender}")
        # No reply by default, unless overridden in a subclass
