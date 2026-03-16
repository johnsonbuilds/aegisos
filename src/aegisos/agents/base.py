import asyncio
import logging
import uuid
from typing import List, Dict, Any, Optional, Type, Union
from pydantic import BaseModel, Field
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.actions import AACPAction
from aegisos.core.llm import BaseLLMEngine
from aegisos.core.config import CONFIG
from aegisos.memory.manager import MemoryManager

logger = logging.getLogger("AACPAgent")

class AACPResponse(BaseModel):
    """
    A streamlined structured output model returned after LLM reasoning.
    Used to guide the Agent in generating a complete AACPMessage.
    """
    receiver: Optional[str] = Field(None, description="URI of the target receiver or 'BROADCAST'. If None, no message is sent.")
    intent: AACPIntent = Field(default=AACPIntent.INFORM, description="Message intent (REQUEST, INFORM, REPLY, etc.)")
    action: Optional[AACPAction] = Field(None, description="Standard Action (optional). If provided, it will be filled into payload['action']")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Specific business data or instruction content")
    context_pointer: Optional[str] = Field(None, description="File path in the Workspace (for passing large data)")
    thought: Optional[str] = Field(None, description="Internal reasoning process of the Agent (Chain of Thought)")

class AACPAgent:
    """
    Base class for Agents with cognitive capabilities.
    """
    def __init__(
        self, 
        role: str, 
        llm_engine: BaseLLMEngine, 
        system_prompt: str,
        agent_id: Optional[str] = None,
        dispatcher: Optional[Any] = None,
        workspace: Optional[Any] = None,
        max_memory_messages: int = 15
    ):
        # If agent_id is not provided, generate it based on role and uuid
        if not agent_id:
            uid = str(uuid.uuid4())[:8]
            self.agent_id = f"{role}_{uid}@{CONFIG.instance_id}"
        else:
            if "@" not in agent_id:
                self.agent_id = f"{agent_id}@{CONFIG.instance_id}"
            else:
                self.agent_id = agent_id

        self.role = role
        self.llm = llm_engine
        self.system_prompt = system_prompt
        self.dispatcher = dispatcher
        self.workspace = workspace
        
        # Lazy load SandboxRunner
        from aegisos.core.sandbox import SandboxRunner
        self.sandbox = SandboxRunner(str(workspace.root_path)) if workspace else None
        
        # Use MemoryManager to manage hot memory
        self.memory = MemoryManager(
            max_messages=max_memory_messages, 
            system_prompt=system_prompt
        )

    def register_to(self, dispatcher: Any):
        """Register itself to the specified Dispatcher."""
        self.dispatcher = dispatcher
        dispatcher.register_agent(self.agent_id, self.handle_message)
        logger.info(f"Agent {self.agent_id} registered to dispatcher.")

    async def handle_message(self, message: AACPMessage):
        """
        Process incoming AACP messages: record history and trigger reasoning.
        """
        logger.info(f"[{self.agent_id}] Received message from {message.sender}: {message.intent}")
        
        # Convert AACP message to text understandable by LLM
        # Note: Here we only record the payload; large data is handled asynchronously via context_pointer
        msg_str = (
            f"FROM: {message.sender}\n"
            f"INTENT: {message.intent}\n"
            f"PAYLOAD: {message.payload}\n"
        )
        if message.context_pointer:
            msg_str += f"CONTEXT_POINTER: {message.context_pointer}\n"

        # Record to memory
        await self.memory.add_message(role="user", content=msg_str)
        
        # Automatically trigger a reaction
        await self.think()

    async def think(self):
        """
        Core reasoning loop: call LLM to decide the next action.
        """
        logger.debug(f"[{self.agent_id}] Thinking...")
        
        try:
            # Enforce Structured Outputs
            response: AACPResponse = await self.llm.generate(
                messages=self.memory.get_context(),
                response_model=AACPResponse
            )
            
            # Record the Agent's own reasoning and actions
            action_desc = f"THOUGHT: {response.thought}\n"
            if response.receiver:
                action_desc += f"ACTION: {response.intent} to {response.receiver}"
            else:
                action_desc += "ACTION: No further action required."
                
            # Record the assistant's reply to memory
            await self.memory.add_message(role="assistant", content=action_desc)

            if not response.receiver:
                logger.info(f"[{self.agent_id}] No action decided.")
                return

            # If the LLM specifies a standard Action, inject it into the payload
            if response.action:
                response.payload["action"] = response.action.value

            # --- Special Logic: Self-executing Reflexion loop ---
            # If the Agent decides to send a REQUEST of type CODE_EXEC to itself, run it directly in the sandbox
            is_self_exec = (
                response.receiver == self.agent_id and 
                response.intent == AACPIntent.REQUEST and 
                (response.payload.get("action") in [AACPAction.CODE_EXEC, AACPAction.PYTHON_RUN])
            )

            if is_self_exec:
                logger.info(f"[{self.agent_id}] Triggering self-execution (Reflexion loop).")
                code = response.payload.get("code", "")
                if self.sandbox and code:
                    result = await self.sandbox.run_python(code)
                    # Store the result in memory as feedback
                    result_msg = (
                        f"EXECUTION_RESULT:\n"
                        f"EXIT_CODE: {result.exit_code}\n"
                        f"STDOUT: {result.stdout}\n"
                        f"STDERR: {result.stderr}\n"
                    )
                    await self.memory.add_message(role="user", content=result_msg)
                    # Recursively trigger reasoning until the Agent considers the task complete
                    await self.think()
                else:
                    logger.error(f"[{self.agent_id}] Sandbox not available or code is empty.")
                return
            # ------------------------------------

            logger.info(f"[{self.agent_id}] Decision: {response.intent} -> {response.receiver}")

            # Construct and send the actual AACPMessage
            out_msg = AACPMessage(
                sender=self.agent_id,
                receiver=response.receiver,
                intent=response.intent,
                payload=response.payload,
                context_pointer=response.context_pointer
            )

            if self.dispatcher:
                await self.dispatcher.send_message(out_msg)
            else:
                logger.warning(f"[{self.agent_id}] No dispatcher connected. Message dropped.")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Thinking failed: {e}", exc_info=True)
            # Send error message feedback
            if self.dispatcher:
                error_msg = AACPMessage(
                    sender=self.agent_id,
                    receiver="BROADCAST",
                    intent=AACPIntent.ERROR,
                    payload={"error": str(e)}
                )
                await self.dispatcher.send_message(error_msg)
