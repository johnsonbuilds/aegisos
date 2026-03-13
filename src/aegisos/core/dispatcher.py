import asyncio
import logging
from typing import Dict, Callable, Coroutine, Any, Optional
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.llm import BaseLLMEngine
from aegisos.core.config import CONFIG, NetworkMode

# 配置日志
logging.basicConfig(level=CONFIG.log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AegisDispatcher")

class AegisDispatcher:
    SYSTEM_AGENT_ID = "system@local"

    def __init__(self, default_llm: Optional[BaseLLMEngine] = None):
        self.agents: Dict[str, Callable[[AACPMessage], Coroutine[Any, Any, None]]] = {}
        self.queue: asyncio.Queue[AACPMessage] = asyncio.Queue()
        self._is_running = False
        self._loop_task: Optional[asyncio.Task] = None
        self.default_llm = default_llm
        
        # 注册系统代理
        self.register_agent(self.SYSTEM_AGENT_ID, self._system_agent_callback)

    def register_agent(self, agent_id: str, callback: Callable[[AACPMessage], Coroutine[Any, Any, None]]):
        """
        注册 Agent 及其异步回调函数。
        """
        if agent_id in self.agents:
            logger.warning(f"Agent {agent_id} is already registered. Overwriting.")
        self.agents[agent_id] = callback
        logger.info(f"Agent '{agent_id}' registered.")

    def unregister_agent(self, agent_id: str):
        """取消注册 Agent"""
        if agent_id in self.agents:
            if agent_id == self.SYSTEM_AGENT_ID:
                logger.error("Cannot unregister system agent!")
                return
            del self.agents[agent_id]
            logger.info(f"Agent '{agent_id}' unregistered.")

    async def send_message(self, message: AACPMessage):
        """
        向队列发送 AACP 消息。
        """
        await self.queue.put(message)
        logger.debug(f"Message {message.message_id} from {message.sender} to {message.receiver} queued.")

    async def start(self):
        """启动事件循环"""
        if self._is_running:
            return
        
        self._is_running = True
        self._loop_task = asyncio.create_task(self._event_loop())
        logger.info(f"AegisDispatcher started on instance: {CONFIG.instance_id}")

    async def stop(self):
        """停止事件循环"""
        self._is_running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        logger.info("AegisDispatcher stopped.")

    async def _event_loop(self):
        """核心事件处理循环"""
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
        """将消息分发给目标 Agent"""
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
            # 识别远程 URI: {role}_{uuid}@{instance_id}
            await self.send_to_remote(target, message)
        else:
            logger.error(f"Target Agent '{target}' not found. Message {message.message_id} dropped.")

    async def send_to_remote(self, receiver_uri: str, message: AACPMessage):
        """
        跨机通信抽象层 (Egress Gateway)
        """
        try:
            _, instance_id = receiver_uri.split("@")
        except ValueError:
            logger.error(f"Invalid receiver URI format: {receiver_uri}")
            return

        if instance_id == CONFIG.instance_id or instance_id == "local":
            # 如果 instance_id 匹配当前实例，理论上应该在 self.agents 中，能走到这里说明未注册
            logger.warning(f"Local delivery failed for {receiver_uri}, agent not registered.")
            return

        # 根据配置的网络模式进行转发
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
        """执行 Agent 回调"""
        try:
            await callback(message)
        except Exception as e:
            logger.error(f"Error executing callback for Agent '{name}': {e}", exc_info=True)

    async def _system_agent_callback(self, message: AACPMessage):
        """
        内置系统代理回调，处理 SPAWN 和 TERMINATE 请求。
        """
        from aegisos.agents.base import AACPAgent

        logger.info(f"[SYSTEM] Handling message from {message.sender}: {message.intent}")
        
        if message.intent == AACPIntent.SPAWN:
            # 获取请求中指定的角色和 Prompt
            role = message.payload.get("role", "assistant")
            system_prompt = message.payload.get("prompt", "You are a helpful assistant.")
            
            # 使用默认 LLM Engine 实例化 Agent
            if not self.default_llm:
                logger.error("[SYSTEM] SPAWN failed: No default LLM engine configured in Dispatcher.")
                return

            new_agent = AACPAgent(
                role=role,
                llm_engine=self.default_llm,
                system_prompt=system_prompt,
                dispatcher=self
            )
            
            # 注册新 Agent
            self.register_agent(new_agent.agent_id, new_agent.handle_message)
            
            # 回复发送者：成功孵化
            reply = AACPMessage(
                sender=self.SYSTEM_AGENT_ID,
                receiver=message.sender,
                intent=AACPIntent.INFORM,
                payload={"status": "SPAWNED", "agent_id": new_agent.agent_id}
            )
            await self.send_message(reply)
            logger.info(f"[SYSTEM] Spawned new agent: {new_agent.agent_id}")

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
