import asyncio
import logging
from typing import Dict, Callable, Coroutine, Any, Optional
from aegisos.core.protocol import AACPMessage, AACPIntent

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AegisDispatcher")

class AegisDispatcher:
    SYSTEM_AGENT_ID = "system@local"

    def __init__(self):
        self.agents: Dict[str, Callable[[AACPMessage], Coroutine[Any, Any, None]]] = {}
        self.queue: asyncio.Queue[AACPMessage] = asyncio.Queue()
        self._is_running = False
        self._loop_task: Optional[asyncio.Task] = None
        
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
        logger.info("AegisDispatcher started.")

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
        else:
            logger.error(f"Target Agent '{target}' not found. Message {message.message_id} dropped.")

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
        logger.info(f"[SYSTEM] Handling message from {message.sender}: {message.intent}")
        
        if message.intent == AACPIntent.SPAWN:
            # 获取请求中指定的 Agent ID 和回调函数 (Mock 实现)
            agent_id = message.payload.get("agent_id")
            # 在真实场景中，这里会根据类型实例化对象。目前我们要求在 payload 里带上临时回调。
            callback = message.payload.get("callback")
            
            if agent_id and callback:
                self.register_agent(agent_id, callback)
                # 回复发送者：成功孵化
                reply = AACPMessage(
                    sender=self.SYSTEM_AGENT_ID,
                    receiver=message.sender,
                    intent=AACPIntent.INFORM,
                    payload={"status": "SPAWNED", "agent_id": agent_id}
                )
                await self.send_message(reply)
            else:
                logger.error(f"[SYSTEM] SPAWN failed: Missing agent_id or callback in payload.")

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
