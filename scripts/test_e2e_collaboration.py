import asyncio
import os
import shutil
import logging
from pathlib import Path
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.core.workspace import WorkspaceManager
from aegisos.core.dispatcher import AegisDispatcher

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(name)s: %(message)s')
logger = logging.getLogger("E2E_Test")

class DummyPMAgent:
    def __init__(self, dispatcher: AegisDispatcher, workspace: WorkspaceManager):
        self.dispatcher = dispatcher
        self.workspace = workspace
        self.name = "PM"

    async def handle_message(self, message: AACPMessage):
        logger.info(f"[{self.name}] Received message from {message.sender}: {message.intent}")
        if message.intent == AACPIntent.INFORM and message.sender == "Coder":
            logger.info(f"[{self.name}] Coder says it's done: {message.payload.get('status')}")

    async def start_task(self):
        logger.info(f"[{self.name}] Starting task: creating requirement...")
        # 1. 写入 req.txt
        content = "Requirement: Write a simple calculator in Python."
        filepath = await self.workspace.write_file("req.txt", content)
        
        # 2. 发送 TASK_COMPLETE 给 Coder
        msg = AACPMessage(
            sender=self.name,
            receiver="Coder",
            intent=AACPIntent.TASK_COMPLETE,
            payload={"task": "create_requirement"},
            context_pointer=filepath
        )
        logger.info(f"[{self.name}] Sending TASK_COMPLETE to Coder with pointer: {filepath}")
        await self.dispatcher.send_message(msg)

class DummyCoderAgent:
    def __init__(self, dispatcher: AegisDispatcher, workspace: WorkspaceManager):
        self.dispatcher = dispatcher
        self.workspace = workspace
        self.name = "Coder"

    async def handle_message(self, message: AACPMessage):
        logger.info(f"[{self.name}] Received message from {message.sender}: {message.intent}")
        if message.intent == AACPIntent.TASK_COMPLETE and message.sender == "PM":
            # 1. 读取需求
            req_path = message.context_pointer
            req_content = await self.workspace.read_file(req_path)
            logger.info(f"[{self.name}] Read requirement from {req_path}: {req_content}")
            
            # 2. “写代码”
            code_content = "print('Welcome to AegisOS Calculator')\ndef add(a, b): return a + b\nprint(add(1, 2))"
            code_path = await self.workspace.write_file("code.py", code_content)
            logger.info(f"[{self.name}] Code written to {code_path}")
            
            # 3. 回复 PM
            reply = AACPMessage(
                sender=self.name,
                receiver="PM",
                intent=AACPIntent.INFORM,
                payload={"status": "Code is ready", "file": code_path}
            )
            await self.dispatcher.send_message(reply)

async def main():
    # 初始化组件
    workspace_base = "_workspace_e2e"
    if os.path.exists(workspace_base):
        shutil.rmtree(workspace_base)
    
    workspace = WorkspaceManager(base_dir=workspace_base, session_id="e2e-session")
    dispatcher = AegisDispatcher()
    
    # 初始化 Agent
    pm = DummyPMAgent(dispatcher, workspace)
    coder = DummyCoderAgent(dispatcher, workspace)
    
    # 注册回调
    dispatcher.register_agent(pm.name, pm.handle_message)
    dispatcher.register_agent(coder.name, coder.handle_message)
    
    # 启动调度器
    await dispatcher.start()
    
    # 启动 E2E 流程：PM 发起任务
    await pm.start_task()
    
    # 给一点时间让消息处理完成
    await asyncio.sleep(1)
    
    # 验证结果
    files = await workspace.list_files()
    logger.info(f"Files in workspace: {files}")
    
    if "req.txt" in files and "code.py" in files:
        logger.info("E2E SUCCESS: Both requirement and code files generated.")
    else:
        logger.error("E2E FAILED: Missing files.")
    
    # 停止调度器
    await dispatcher.stop()
    logger.info("E2E Test completed.")

if __name__ == "__main__":
    asyncio.run(main())
