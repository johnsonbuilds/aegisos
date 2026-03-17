import asyncio
import os
import logging
from aegisos.core.dispatcher import AegisDispatcher
from aegisos.core.workspace import WorkspaceManager
from aegisos.core.llm import OpenAIEngine
from aegisos.core.protocol import AACPMessage, AACPIntent
from aegisos.agents.common import CoordinatorAgent
from aegisos.core.config import CONFIG

# Configure logging to see the message flow
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("Task8Demo")

async def main():
    # 1. Setup Workspace
    workspace_dir = "./demo_workspace"
    if not os.path.exists(workspace_dir):
        os.makedirs(workspace_dir)
    workspace = WorkspaceManager(workspace_dir)
    logger.info(f"Workspace initialized at {workspace_dir}")

    # 2. Setup LLM Engine (Uses environment variables by default)
    # Ensure OPENAI_API_KEY is set in your environment
    if not CONFIG.openai_api_key:
        logger.error("OPENAI_API_KEY not found in environment. Please set it to run the demo.")
        return
        
    llm = OpenAIEngine()
    logger.info(f"LLM Engine initialized using model: {llm.model}")

    # 3. Setup Dispatcher
    dispatcher = AegisDispatcher(default_llm=llm, workspace=workspace)
    await dispatcher.start()
    logger.info("Dispatcher started.")

    # 4. Create and register Coordinator Agent
    coordinator = CoordinatorAgent(llm_engine=llm, workspace=workspace)
    coordinator.register_to(dispatcher)
    logger.info(f"CoordinatorAgent registered as {coordinator.agent_id}")

    # 5. Simulate User Request
    user_goal = "Fetch the main page of https://www.indiehackers.com/ and generate a summary report of current top stories."
    
    user_msg = AACPMessage(
        sender="user@local", # Fixed URI format
        receiver=coordinator.agent_id,
        intent=AACPIntent.INFORM,
        payload={"goal": user_goal}
    )
    
    logger.info(f"Sending user goal to coordinator: {user_goal}")
    await dispatcher.send_message(user_msg)

    # 6. Keep the demo running for a while to see the collaboration
    # In a real app, we would wait for a specific TERMINATE or TASK_COMPLETE message
    try:
        logger.info("Running collaboration loop (Ctrl+C to stop)...")
        # Run for 120 seconds or until finished
        await asyncio.sleep(120) 
    except KeyboardInterrupt:
        logger.info("Demo stopped by user.")
    finally:
        await dispatcher.stop()
        logger.info("Dispatcher stopped.")

if __name__ == "__main__":
    asyncio.run(main())
