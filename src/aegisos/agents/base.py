import asyncio
import logging
import uuid
import json
from typing import List, Dict, Any, Optional, Type, Union
from pydantic import BaseModel, Field, field_validator
from aegisos.core.protocol import AACPMessage, AACPIntent, parse_agent_uri
from aegisos.core.actions import AACPAction
from aegisos.core.llm import BaseLLMEngine
from aegisos.core.config import CONFIG
from aegisos.core.skills import BaseSkill, SkillResult
from aegisos.memory.manager import MemoryManager

logger = logging.getLogger("AACPAgent")

class AACPResponse(BaseModel):
    """
    A streamlined structured output model returned after LLM reasoning.
    Used to guide the Agent in generating a complete AACPMessage.
    """
    receiver: Optional[str] = Field(None, description="URI of the target receiver or 'BROADCAST'. If None, no message is sent.")
    intent: AACPIntent = Field(AACPIntent.INFORM, description="Message intent (REQUEST, INFORM, REPLY, etc.)")
    action: Optional[Dict[str, Any]] = Field(None, description="Structured Action: {'name': '...', 'args': {...}}. Mandatory for REQUEST.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Transient data (non-persistent)")
    context_pointer: Optional[Union[str, Dict[str, Any]]] = Field(None, description="Cognitive state pointer (index + directive)")
    thought: Optional[str] = Field(None, description="Internal reasoning process (Chain of Thought)")

    @field_validator("payload", mode="before")
    @classmethod
    def normalize_payload(cls, value: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if value is None:
            return {}
        return value


class AACPAgent:
    """
    Base class for Agents with cognitive capabilities.
    """
    requires_llm = True # Class metadata for Factory/Dispatcher

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
        # ... (agent_id generation logic)
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
        
        # Runtime State
        self.current_step = 0
        self._is_shutdown = False
        self._last_message_sender: Optional[str] = None
        self._last_context_pointer: Optional[Union[str, Dict[str, Any]]] = None
        self._last_message_payload: Dict[str, Any] = {}
        self._last_action_name: Optional[str] = None
        self._last_action_result: Optional[Any] = None
        
        # Lazy load SandboxRunner
        from aegisos.core.sandbox import SandboxRunner
        self.sandbox = SandboxRunner(str(workspace.root_path)) if workspace else None
        
        # Skill Registry
        self.skills: Dict[str, BaseSkill] = {}
        
        # Register default internal skills
        from aegisos.agents.skills.file_system import FileSystemSkill
        self.add_skill(FileSystemSkill(AACPAction.FILE_WRITE.value))
        self.add_skill(FileSystemSkill(AACPAction.FILE_READ.value))
        
        # Use MemoryManager to manage hot memory
        self.memory = MemoryManager(
            max_messages=max_memory_messages, 
            system_prompt=system_prompt
        )

    def add_skill(self, skill: BaseSkill):
        """Register a new skill to this agent."""
        if not skill.check_dependencies():
            logger.error(f"[{self.agent_id}] Failed to load skill {skill.name}: Missing dependencies.")
            return False
        self.skills[skill.name] = skill
        logger.info(f"[{self.agent_id}] Skill {skill.name} registered.")
        return True

    def register_to(self, dispatcher: Any):
        """Register itself to the specified Dispatcher."""
        self.dispatcher = dispatcher
        dispatcher.register_agent(self.agent_id, self.handle_message)
        logger.info(f"Agent {self.agent_id} registered to dispatcher.")

    async def handle_message(self, message: AACPMessage):
        """
        Process incoming AACP messages: inject minimal context index and record history.
        """
        if self._is_shutdown:
            logger.debug(f"[{self.agent_id}] Ignored message (Agent is shut down).")
            return

        logger.info(f"[{self.agent_id}] Received message from {message.sender}: {message.intent}")
        self._last_message_sender = message.sender
        self._last_context_pointer = message.context_pointer
        self._last_message_payload = message.payload.copy() if isinstance(message.payload, dict) else {}
        
        # Reset loop counter on new external instruction
        self.current_step = 0
        
        # --- Message Representation for LLM ---
        msg_str = (
            f"FROM: {message.sender}\n"
            f"INTENT: {message.intent}\n"
            f"PAYLOAD: {json.dumps(message.payload)}\n"
        )
        
        # --- Cognitive Architecture: Minimal Context Index ---
        if message.context_pointer:
            msg_str += self._format_cognitive_index(message.context_pointer)

        # Record to memory
        await self.memory.add_message(role="user", content=msg_str)
        
        # Automatically trigger a reaction
        await self.think()

    def _format_cognitive_index(self, context_pointer: Union[str, Dict[str, Any]]) -> str:
        """Standardized Index + Directive formatting for the prompt."""
        if isinstance(context_pointer, dict):
            cur_task = context_pointer.get("current_task", "N/A")
            uri = context_pointer.get("uri", "unknown")
            ctx_type = context_pointer.get("type", "unknown")
            
            return (
                f"\n[COGNITIVE CONTEXT INDEX]\n"
                f"Directive: {cur_task}\n"
                f"Available State Reference: {uri} (Type: {ctx_type})\n"
                f"NOTE: Use 'core.fs.read' if you need full details.\n"
            )
        else:
            return f"\nCONTEXT_POINTER (URI): {context_pointer}\n"

    def _clone_context_pointer(
        self,
        context_pointer: Optional[Union[str, Dict[str, Any]]],
    ) -> Optional[Union[str, Dict[str, Any]]]:
        if isinstance(context_pointer, dict):
            return context_pointer.copy()
        return context_pointer

    async def _augment_outgoing_payload(
        self,
        payload: Dict[str, Any],
        response: AACPResponse,
        target_uri: str,
    ) -> Dict[str, Any]:
        return payload

    async def _augment_outgoing_context_pointer(
        self,
        context_pointer: Optional[Union[str, Dict[str, Any]]],
        response: AACPResponse,
        target_uri: str,
    ) -> Optional[Union[str, Dict[str, Any]]]:
        return context_pointer

    async def _promote_action_artifact(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        output_path = self._last_message_payload.get("output_path")
        source_path = result_data.get("context_pointer")
        if not output_path or not source_path or not self.workspace:
            return result_data
        if output_path == source_path:
            return result_data

        try:
            content = await self.workspace.read_file(source_path)
            await self.workspace.write_file(output_path, content)
            result_data = result_data.copy()
            result_data["source_context_pointer"] = source_path
            result_data["context_pointer"] = output_path
            result_data["artifact_path"] = output_path
            result_data["message"] = f"Successfully materialized artifact to {output_path}"
        except Exception as exc:
            logger.warning(f"[{self.agent_id}] Failed to promote action artifact to {output_path}: {exc}")

        return result_data

    def _summarize_result_for_feedback(self, result_data: Dict[str, Any]) -> Dict[str, Any]:
        summary = result_data.copy()
        content = summary.get("content")
        if isinstance(content, str) and len(content) > 4000:
            summary["content"] = content[:4000] + "\n...[truncated for prompt safety]"
            summary["content_truncated"] = True
            summary["content_length"] = len(content)
        return summary

    async def close(self):
        """Release agent resources."""
        if self._is_shutdown:
            return
        self._is_shutdown = True
        logger.info(f"[{self.agent_id}] Shutting down...")

    async def _shutdown_and_unregister(self):
        """Idempotently close the agent and remove it from the dispatcher registry."""
        await self.close()
        if self.dispatcher and hasattr(self.dispatcher, "unregister_agent"):
            try:
                await self.dispatcher.unregister_agent(self.agent_id)
            except Exception as e:
                logger.error(f"[{self.agent_id}] Failed to unregister during shutdown: {e}")

    async def think(self):
        """
        Core reasoning loop: call LLM and enforce AACP Payload/Context separation.
        """
        if self._is_shutdown:
            logger.warning(f"[{self.agent_id}] think() called after shutdown. Aborting.")
            return

        self.current_step += 1
        if self.current_step > CONFIG.agent_max_steps:
            err_msg = f"Max steps ({CONFIG.agent_max_steps}) exceeded in reasoning loop."
            logger.error(f"[{self.agent_id}] {err_msg}")
            
            if self.dispatcher:
                await self.dispatcher.send_message(AACPMessage(
                    sender=self.agent_id,
                    receiver="BROADCAST",
                    intent=AACPIntent.ERROR,
                    payload={"error": err_msg, "step": self.current_step}
                ))
            
            await self._shutdown_and_unregister()
            return

        logger.debug(f"[{self.agent_id}] Thinking (Step {self.current_step})...")
        
        try:
            # Prepare messages
            original_messages = self.memory.get_context()
            messages = [m.copy() for m in original_messages]
            
            # Inject available skills into the first system message
            if self.skills:
                skills_desc = "\nAVAILABLE SKILLS (JSON):\n" + json.dumps(
                    [skill.describe() for skill in self.skills.values()],
                    indent=2,
                    ensure_ascii=False,
                )
                if messages and messages[0]["role"] == "system":
                    # Check if already injected to avoid duplicates
                    if "AVAILABLE SKILLS (JSON):" not in messages[0]["content"]:
                        messages[0]["content"] += skills_desc

            # Enforce Structured Outputs
            response: AACPResponse = await self.llm.generate(
                messages=messages,
                response_model=AACPResponse
            )
            
            logger.info(f"[{self.agent_id}] Thought: {response.thought}")
            
            # --- Enforce Payload/Context Separation ---
            final_payload = response.payload.copy()
            if response.action:
                final_payload["action"] = response.action

            # Record reasoning in memory
            action_desc = f"THOUGHT: {response.thought}\n"
            if response.receiver:
                action_desc += f"DECISION: {response.intent} to {response.receiver}\n"
                if response.action:
                    action_desc += f"ACTION: {json.dumps(response.action)}\n"
            else:
                action_desc += "DECISION: No further action required."
                
            await self.memory.add_message(role="assistant", content=action_desc)

            # If an action is provided but no receiver, assume self-execution (Reflexion)
            target_uri = response.receiver
            if response.action and not target_uri:
                target_uri = self.agent_id
                logger.debug(f"[{self.agent_id}] Action provided without receiver. Defaulting to self-execution.")

            if not target_uri:
                return

            response_context_pointer = self._clone_context_pointer(response.context_pointer)
            final_payload = await self._augment_outgoing_payload(final_payload, response, target_uri)
            response_context_pointer = await self._augment_outgoing_context_pointer(
                response_context_pointer,
                response,
                target_uri,
            )

            # --- Special Logic: Self-executing Action loop (Reflexion) ---
            role, inst, _ = parse_agent_uri(target_uri) if target_uri else (None, None, None)
            is_self_exec = (
                target_uri == self.agent_id or 
                (role == self.role and inst in ["local", CONFIG.instance_id])
            )

            if is_self_exec and (response.intent == AACPIntent.REQUEST or response.action):
                action_obj = response.action
                action_name = action_obj.get("name") if action_obj else "unknown"
                logger.info(f"[{self.agent_id}] Triggering self-execution: {action_name}")
                
                success = False
                result_content = ""
                
                if action_name in self.skills:
                    skill_res = await self.skills[action_name].execute(
                        payload=action_obj.get("args", {}),
                        context={
                            "workspace_path": str(self.workspace.root_path) if self.workspace else None,
                            "agent_id": self.agent_id
                        }
                    )
                    success = skill_res.success
                    self._last_action_name = action_name
                    self._last_action_result = skill_res.data if success else skill_res.error
                    if success and isinstance(skill_res.data, dict):
                        skill_res.data = await self._promote_action_artifact(skill_res.data)
                        self._last_action_result = skill_res.data
                    if success and isinstance(skill_res.data, dict):
                        result_content = json.dumps(self._summarize_result_for_feedback(skill_res.data))
                    else:
                        result_content = json.dumps(skill_res.data) if success else str(skill_res.error)
                elif action_name in [AACPAction.CODE_EXEC.value, AACPAction.PYTHON_RUN.value]:
                    code = action_obj.get("args", {}).get("code", "")
                    if self.sandbox and code:
                        sandbox_res = await self.sandbox.run_python(code)
                        success = (sandbox_res.exit_code == 0)
                        self._last_action_name = action_name
                        self._last_action_result = sandbox_res.stdout if success else sandbox_res.stderr
                        result_content = sandbox_res.stdout if success else f"STDOUT: {sandbox_res.stdout}\nSTDERR: {sandbox_res.stderr}"
                    else:
                        result_content = "ERROR: Sandbox not available or code is empty."
                else:
                    result_content = f"ERROR: Unknown action or skill '{action_name}'"

                # --- Reflexion: Index + Directive pattern (Externalized Results/Errors) ---
                if not success:
                    # Write full error log to workspace
                    error_uri = f"errors/{action_name}_{uuid.uuid4().hex[:4]}.log"
                    if self.workspace:
                        await self.workspace.write_file(error_uri, result_content)
                        feedback = (
                            f"ACTION_FAILURE: '{action_name}' failed.\n"
                            + self._format_cognitive_index({
                                "type": "error",
                                "uri": error_uri,
                                "current_task": f"fix_{action_name}"
                            })
                        )
                    else:
                        feedback = f"ACTION_FAILURE: '{action_name}' failed. Details: {result_content}"
                else:
                    # For success, if result is small, return directly; if large, can be externalized too
                    # (Here we keep it simple: data directly for now unless it's huge)
                    feedback = f"ACTION_SUCCESS: '{action_name}' completed.\nRESULT: {result_content}"
                
                await self.memory.add_message(role="user", content=feedback)
                await self.think() # Reflexive loop
                return
            # ------------------------------------

            # Construct and send the actual AACPMessage
            out_msg = AACPMessage(
                sender=self.agent_id,
                receiver=response.receiver,
                intent=response.intent,
                payload=final_payload,
                context_pointer=response_context_pointer
            )

            if self.dispatcher:
                await self.dispatcher.send_message(out_msg)
            else:
                logger.warning(f"[{self.agent_id}] No dispatcher connected. Message dropped.")
                
        except Exception as e:
            logger.error(f"[{self.agent_id}] Thinking failed: {e}", exc_info=True)
            if self.dispatcher:
                error_msg = AACPMessage(
                    sender=self.agent_id,
                    receiver="BROADCAST",
                    intent=AACPIntent.ERROR,
                    payload={"error": str(e)}
                )
                await self.dispatcher.send_message(error_msg)
