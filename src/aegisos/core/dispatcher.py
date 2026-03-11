import asyncio
import logging
from typing import Dict, Callable, Coroutine, Any, Optional
from aegisos.core.protocol import AACPMessage

# 配置基础日志，方便后续调试
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AegisDispatcher")

class AegisDispatcher:
    def __init__(self):
        self.agents: Dict[str, Callable[[AACPMessage], Coroutine[Any, Any, None]]] = {}
        self.queue: asyncio.Queue[AACPMessage] = asyncio.Queue()
        self._is_running = False
        self._loop_task: Optional[asyncio.Task] = None

    def register_agent(self, agent_name: str, agent_callback: Callable[[AACPMessage], Coroutine[Any, Any, None]]):
        """
        注册 Agent 及其异步回调函数。
        """
        if agent_name in self.agents:
            logger.warning(f"Agent {agent_name} is already registered. Overwriting.")
        self.agents[agent_name] = agent_callback
        logger.info(f"Agent '{agent_name}' registered.")

    def unregister_agent(self, agent_name: str):
        """取消注册 Agent"""
        if agent_name in self.agents:
            del self.agents[agent_name]
            logger.info(f"Agent '{agent_name}' unregistered.")

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
                # 获取下一条消息
                message = await self.queue.get()
                
                # 路由消息
                await self._route_message(message)
                
                # 标记队列任务完成
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in dispatcher event loop: {e}", exc_info=True)

    async def _route_message(self, message: AACPMessage):
        """将消息分发给目标 Agent"""
        target = message.receiver
        
        if target == "BROADCAST":
            # 广播给所有已注册的 Agent
            logger.info(f"Broadcasting message from {message.sender}")
            tasks = [self._call_agent(name, callback, message) 
                     for name, callback in self.agents.items()]
            if tasks:
                await asyncio.gather(*tasks)
        elif target in self.agents:
            # 单播
            await self._call_agent(target, self.agents[target], message)
        else:
            logger.error(f"Target Agent '{target}' not found. Message {message.message_id} dropped.")

    async def _call_agent(self, name: str, callback: Callable, message: AACPMessage):
        """安全地执行 Agent 回调"""
        try:
            await callback(message)
        except Exception as e:
            logger.error(f"Error executing callback for Agent '{name}': {e}", exc_info=True)
