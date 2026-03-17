import logging
from typing import Optional, Any, Dict
from aegisos.agents.base import AACPAgent
from aegisos.core.llm import BaseLLMEngine
from aegisos.core.actions import AACPAction

logger = logging.getLogger("CommonAgents")

COORDINATOR_PROMPT = """You are the AegisOS Coordinator. 
Your goal is to receive a high-level goal from the user, break it down into a specific task, 
and spawn a worker agent to execute it.

Your Agent URI: {agent_id}

Workflow (STRICTLY FOLLOW ARCHITECTURE #7.1):
1. Receive user goal.
2. Formulate a 'task.json' with instructions.
3. Save 'task.json' (Action: core.fs.write). YOU MUST SET RECEIVER TO YOUR OWN URI TO EXECUTE THIS ACTION.
   Example JSON:
   {{
     "thought": "I will save the task details now.",
     "receiver": "{agent_id}",
     "intent": "REQUEST",
     "action": "core.fs.write",
     "payload": {{"path": "task.json", "content": "..."}}
   }}
4. SPAWN a worker agent (Receiver: system@local, Intent: SPAWN, agent_type: worker).
5. Send a REQUEST to the worker with context_pointer="task.json".

NEVER pass large task descriptions in the payload. ALWAYS use context_pointer.
"""

WORKER_PROMPT = """You are an AegisOS Worker Agent.
Your goal is to execute specific tasks assigned by the Coordinator.

Workflow (STRICTLY FOLLOW ARCHITECTURE #5.2):
1. You will receive a REQUEST with a context_pointer.
2. Read the task details from the referenced file (action: core.fs.read).
3. Execute the task using your skills (e.g., core.cog.web_fetch).
4. Note that skills like web_fetch will return a context_pointer to the result file. 
5. Read those result files if needed to summarize or process.
6. Write your final results (e.g., report.md) to the workspace.
7. Send a TASK_COMPLETE message back to the sender with context_pointer to your report.

Skills:
- core.cog.web_fetch: Fetches a URL and saves results to a file in the workspace. Returns the file path.
"""

class CoordinatorAgent(AACPAgent):
    def __init__(self, llm_engine: BaseLLMEngine, **kwargs):
        # Remove 'role' from kwargs if present to avoid collision with explicit role="coordinator"
        kwargs.pop("role", None)
        super().__init__(
            role="coordinator",
            llm_engine=llm_engine,
            system_prompt=COORDINATOR_PROMPT, # Initial prompt
            **kwargs
        )
        # Re-inject agent_id into prompt for clarity
        self.system_prompt = COORDINATOR_PROMPT.format(agent_id=self.agent_id)
        # Update memory with the finalized system prompt
        if self.memory.history and self.memory.history[0].role == "system":
            self.memory.history[0].content = self.system_prompt

class WorkerAgent(AACPAgent):
    def __init__(self, llm_engine: BaseLLMEngine, **kwargs):
        # Remove 'role' from kwargs if present to avoid collision with explicit role="worker"
        kwargs.pop("role", None)
        super().__init__(
            role="worker",
            llm_engine=llm_engine,
            system_prompt=WORKER_PROMPT,
            **kwargs
        )
        # Workers usually have specific skills
        from aegisos.agents.skills.web_scraper import WebScraperSkill
        self.add_skill(WebScraperSkill())
