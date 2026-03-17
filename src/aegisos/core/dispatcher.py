import asyncio
import logging
from typing import Dict, Callable, Coroutine, Any, Optional
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.llm import BaseLLMEngine
from aegisos.core.config import CONFIG, NetworkMode

# Configure logging
logging.basicConfig(level=CONFIG.log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AegisDispatcher")

class AegisDispatcher:
    SYSTEM_AGENT_ID = "system@local"

    def __init__(self, default_llm: Optional[BaseLLMEngine] = None, workspace: Optional[Any] = None):
        self.agents: Dict[str, Callable[[AACPMessage], Coroutine[Any, Any, None]]] = {}
        self.queue: asyncio.Queue[AACPMessage] = asyncio.Queue()
        self._is_running = False
        self._loop_task: Optional[asyncio.Task] = None
        self.default_llm = default_llm
        self.workspace = workspace
        
        # Register system agent
        self.register_agent(self.SYSTEM_AGENT_ID, self._system_agent_callback)

    def register_agent(self, agent_id: str, callback: Callable[[AACPMessage], Coroutine[Any, Any, None]]):
        """
        Register an Agent and its asynchronous callback function.
        """
        if agent_id in self.agents:
            logger.warning(f"Agent {agent_id} is already registered. Overwriting.")
        self.agents[agent_id] = callback
        logger.info(f"Agent '{agent_id}' registered.")

    def unregister_agent(self, agent_id: str):
        """Unregister an Agent."""
        if agent_id in self.agents:
            if agent_id == self.SYSTEM_AGENT_ID:
                logger.error("Cannot unregister system agent!")
                return
            del self.agents[agent_id]
            logger.info(f"Agent '{agent_id}' unregistered.")

    async def send_message(self, message: AACPMessage):
        """
        Send an AACP message to the queue.
        """
        await self.queue.put(message)
        logger.debug(f"Message {message.message_id} from {message.sender} to {message.receiver} queued.")

    async def start(self):
        """Start the event loop."""
        if self._is_running:
            return
        
        self._is_running = True
        self._loop_task = asyncio.create_task(self._event_loop())
        logger.info(f"AegisDispatcher started on instance: {CONFIG.instance_id}")

    async def stop(self):
        """Stop the event loop."""
        self._is_running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        logger.info("AegisDispatcher stopped.")

    async def _event_loop(self):
        """Core event processing loop."""
        while self._is_running:
            try:
                message = await self.queue.get()
                await self._route_message(message)
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in dispatcher event loop: {e}", exc_info=True)

    async def _route_message(self, message: AACPMessage):
        """Dispatch message to the target Agent."""
        target = message.receiver
        
        if target == "BROADCAST":
            logger.info(f"Broadcasting message from {message.sender}")
            tasks = [self._call_agent(name, callback, message) 
                     for name, callback in self.agents.items()]
            if tasks:
                await asyncio.gather(*tasks)
        elif target in self.agents:
            await self._call_agent(target, self.agents[target], message)
        elif "@" in target:
            # Identify remote URI: {role}_{uuid}@{instance_id}
            await self.send_to_remote(target, message)
        else:
            logger.error(f"Target Agent '{target}' not found. Message {message.message_id} dropped.")

    async def send_to_remote(self, receiver_uri: str, message: AACPMessage):
        """
        Cross-instance communication abstraction layer (Egress Gateway).
        """
        try:
            _, instance_id = receiver_uri.split("@")
        except ValueError:
            logger.error(f"Invalid receiver URI format: {receiver_uri}")
            return

        if instance_id == CONFIG.instance_id or instance_id == "local":
            # If instance_id matches current instance, it should theoretically be in self.agents;
            # reaching here means it's not registered.
            logger.warning(f"Local delivery failed for {receiver_uri}, agent not registered.")
            return

        # Forward based on configured network mode
        if CONFIG.network_mode == NetworkMode.LOCAL:
            logger.warning(f"Network mode is LOCAL. Cannot send to remote instance: {instance_id}")
        elif CONFIG.network_mode == NetworkMode.TAILSCALE:
            logger.info(f"Mock: Sending to {instance_id} via Tailscale (gRPC/P2P)")
        elif CONFIG.network_mode == NetworkMode.NOSTR:
            logger.info(f"Mock: Sending to {instance_id} via Nostr Relay")
        elif CONFIG.network_mode == NetworkMode.LIBP2P:
            logger.info(f"Mock: Sending to {instance_id} via libp2p DHT")
        else:
            logger.error(f"Unsupported network mode: {CONFIG.network_mode}")

    async def _call_agent(self, name: str, callback: Callable, message: AACPMessage):
        """Execute Agent callback."""
        try:
            await callback(message)
        except Exception as e:
            logger.error(f"Error executing callback for Agent '{name}': {e}", exc_info=True)

    async def _system_agent_callback(self, message: AACPMessage):
        """
        Built-in system agent callback, handling SPAWN and TERMINATE requests.
        """
        from aegisos.core.factory import AGENT_FACTORY

        logger.info(f"[SYSTEM] Handling message from {message.sender}: {message.intent}")
        
        if message.intent == AACPIntent.SPAWN:
            agent_type = message.payload.get("agent_type", "llm")
            role = message.payload.get("role", "assistant")
            requested_id = message.payload.get("agent_id")
            
            # Prepare creation parameters
            spawn_params = {
                "role": role,
                "agent_id": requested_id,
                "dispatcher": self,
                "workspace": self.workspace 
            }
            
            try:
                # 1. Inspect class metadata (Architecture #12 & #13)
                agent_class = AGENT_FACTORY.get_class(agent_type)
                
                # Check for LLM requirement
                if getattr(agent_class, "requires_llm", False):
                    if not self.default_llm:
                        logger.error(f"[SYSTEM] SPAWN failed: No default LLM engine for agent type '{agent_type}' which requires it.")
                        return
                    spawn_params["llm_engine"] = self.default_llm
                    
                    # Custom prompt injection
                    if "prompt" in message.payload:
                        spawn_params["system_prompt"] = message.payload["prompt"]

                # 2. Instantiate Agent through Factory
                new_agent = AGENT_FACTORY.create(agent_type, **spawn_params)
                
                # Register new Agent
                self.register_agent(new_agent.agent_id, new_agent.handle_message)
                
                # Reply to sender: success
                reply = AACPMessage(
                    sender=self.SYSTEM_AGENT_ID,
                    receiver=message.sender,
                    intent=AACPIntent.INFORM,
                    payload={"status": "SPAWNED", "agent_id": new_agent.agent_id}
                )
                await self.send_message(reply)
                logger.info(f"[SYSTEM] Spawned new {agent_type} agent: {new_agent.agent_id}")
            except Exception as e:
                logger.error(f"[SYSTEM] SPAWN failed: {e}", exc_info=True)
                return

        elif message.intent == AACPIntent.TERMINATE:
            target_agent_id = message.payload.get("agent_id")
            if target_agent_id:
                self.unregister_agent(target_agent_id)
                reply = AACPMessage(
                    sender=self.SYSTEM_AGENT_ID,
                    receiver=message.sender,
                    intent=AACPIntent.INFORM,
                    payload={"status": "TERMINATED", "agent_id": target_agent_id}
                )
                await self.send_message(reply)
            else:
                logger.error(f"[SYSTEM] TERMINATE failed: Missing agent_id in payload.")
