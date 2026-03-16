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
    LLM 思考后返回的精简结构化输出模型。
    用于指导 Agent 生成完整的 AACPMessage。
    """
    receiver: Optional[str] = Field(None, description="目标接收者的 URI 或 'BROADCAST'。如果为 None 则不发送消息。")
    intent: AACPIntent = Field(default=AACPIntent.INFORM, description="消息意图 (REQUEST, INFORM, REPLY, etc.)")
    action: Optional[AACPAction] = Field(None, description="标准 Action (可选)。如果提供，会填入 payload['action']")
    payload: Dict[str, Any] = Field(default_factory=dict, description="具体的业务数据或指令内容")
    context_pointer: Optional[str] = Field(None, description="Workspace 中的文件路径（如需传递大数据）")
    thought: Optional[str] = Field(None, description="Agent 内部的思考过程 (Chain of Thought)")

class AACPAgent:
    """
    具备认知能力的 Agent 基类。
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
        # 如果未提供 agent_id，则根据 role 和 uuid 生成
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
        
        # 懒加载 SandboxRunner
        from aegisos.core.sandbox import SandboxRunner
        self.sandbox = SandboxRunner(str(workspace.root_path)) if workspace else None
        
        # 使用 MemoryManager 管理热记忆
        self.memory = MemoryManager(
            max_messages=max_memory_messages, 
            system_prompt=system_prompt
        )

    def register_to(self, dispatcher: Any):
        """将自己注册到指定的 Dispatcher"""
        self.dispatcher = dispatcher
        dispatcher.register_agent(self.agent_id, self.handle_message)
        logger.info(f"Agent {self.agent_id} registered to dispatcher.")

    async def handle_message(self, message: AACPMessage):
        """
        处理传入的 AACP 消息：记录历史并触发思考。
        """
        logger.info(f"[{self.agent_id}] Received message from {message.sender}: {message.intent}")
        
        # 将 AACP 消息转为 LLM 可理解的文本
        # 注意：这里我们只记录 payload，大数据通过 context_pointer 异步处理
        msg_str = (
            f"FROM: {message.sender}\n"
            f"INTENT: {message.intent}\n"
            f"PAYLOAD: {message.payload}\n"
        )
        if message.context_pointer:
            msg_str += f"CONTEXT_POINTER: {message.context_pointer}\n"

        # 记录到记忆中
        await self.memory.add_message(role="user", content=msg_str)
        
        # 自动触发反应
        await self.think()

    async def think(self):
        """
        核心思考循环：调用 LLM 决定下一步动作。
        """
        logger.debug(f"[{self.agent_id}] Thinking...")
        
        try:
            # 强制 Structured Outputs
            response: AACPResponse = await self.llm.generate(
                messages=self.memory.get_context(),
                response_model=AACPResponse
            )
            
            # 记录 Agent 自己的思考和动作
            action_desc = f"THOUGHT: {response.thought}\n"
            if response.receiver:
                action_desc += f"ACTION: {response.intent} to {response.receiver}"
            else:
                action_desc += "ACTION: No further action required."
                
            # 记录助手回复到记忆
            await self.memory.add_message(role="assistant", content=action_desc)

            if not response.receiver:
                logger.info(f"[{self.agent_id}] No action decided.")
                return

            # 如果 LLM 指定了标准 Action，将其注入 payload
            if response.action:
                response.payload["action"] = response.action.value

            # --- 特殊逻辑: 自执行的 Reflexion 闭环 ---
            # 如果 Agent 决定向自己发送一个 CODE_EXEC 类型的 REQUEST，则直接在沙箱运行
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
                    # 将结果作为反馈存入记忆
                    result_msg = (
                        f"EXECUTION_RESULT:\n"
                        f"EXIT_CODE: {result.exit_code}\n"
                        f"STDOUT: {result.stdout}\n"
                        f"STDERR: {result.stderr}\n"
                    )
                    await self.memory.add_message(role="user", content=result_msg)
                    # 递归触发思考，直到 Agent 认为任务完成
                    await self.think()
                else:
                    logger.error(f"[{self.agent_id}] Sandbox not available or code is empty.")
                return
            # ------------------------------------

            logger.info(f"[{self.agent_id}] Decision: {response.intent} -> {response.receiver}")

            # 构造并发送真正的 AACPMessage
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
            # 发送错误消息反馈
            if self.dispatcher:
                error_msg = AACPMessage(
                    sender=self.agent_id,
                    receiver="BROADCAST",
                    intent=AACPIntent.ERROR,
                    payload={"error": str(e)}
                )
                await self.dispatcher.send_message(error_msg)
