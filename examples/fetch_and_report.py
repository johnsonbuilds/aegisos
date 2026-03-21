import asyncio
import os
import logging
import uuid
from aegisos.core.dispatcher import AegisDispatcher
from aegisos.core.workspace import WorkspaceManager
from aegisos.core.llm import OpenAIEngine
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.agents.common import CoordinatorAgent, WorkerAgent
from aegisos.core.config import CONFIG

# Force unbuffered output
os.environ["PYTHONUNBUFFERED"] = "1"

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("Task8Demo")

async def main():
    # 1. Setup Workspace with unique session
    session_id = f"demo-{uuid.uuid4().hex[:8]}"
    workspace_dir = f"./demo_workspace/{session_id}"
    workspace = WorkspaceManager(base_dir="./demo_workspace", session_id=session_id)
    logger.info(f"=== DEMO START: {session_id} ===")
    logger.info(f"Workspace: {workspace.root_path}")

    # 2. Setup LLM Engine
    if not CONFIG.openai_api_key:
        logger.error("OPENAI_API_KEY missing.")
        return
    llm = OpenAIEngine()

    # 3. Setup Dispatcher
    dispatcher = AegisDispatcher(default_llm=llm, workspace=workspace)
    await dispatcher.start()

    # 4. Register Agents
    coordinator = CoordinatorAgent(llm_engine=llm, workspace=workspace)
    coordinator.register_to(dispatcher)
    
    web_scraper = WorkerAgent(llm_engine=llm, workspace=workspace)
    web_scraper.register_to(dispatcher)
    dispatcher.register_agent("web_scraper@local", web_scraper.handle_message)

    report_generator = WorkerAgent(llm_engine=llm, workspace=workspace)
    report_generator.register_to(dispatcher)
    dispatcher.register_agent("analyst@local", report_generator.handle_message)
    dispatcher.register_agent("summarizer@local", report_generator.handle_message)
    dispatcher.register_agent("report_generator@local", report_generator.handle_message)

    # 5. User Goal
    user_goal = "Fetch the main page of https://www.indiehackers.com/ and generate a short summary report."
    user_msg = AACPMessage(
        sender="user@local",
        receiver=coordinator.agent_id,
        intent=AACPIntent.INFORM,
        payload={"goal": user_goal}
    )
    await dispatcher.send_message(user_msg)

    # 6. Run loop
    try:
        logger.info("Collaboration started...")
        report_path = workspace.root_path / "indiehackers_summary.txt"
        deadline = asyncio.get_running_loop().time() + 180
        while asyncio.get_running_loop().time() < deadline:
            if report_path.exists():
                logger.info(f"Report generated: {report_path}")
                break
            await asyncio.sleep(2)
    finally:
        await dispatcher.stop()
        logger.info("=== DEMO FINISHED ===")

if __name__ == "__main__":
    asyncio.run(main())
