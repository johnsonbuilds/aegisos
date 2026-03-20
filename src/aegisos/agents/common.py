import json
import logging
from typing import Optional, Any, Dict
from aegisos.agents.base import AACPAgent
from aegisos.core.llm import BaseLLMEngine
from aegisos.core.actions import AACPAction
from aegisos.core.protocol import AACPMessage, AACPIntent

logger = logging.getLogger("CommonAgents")

COORDINATOR_PROMPT = """You are the AegisOS Coordinator. 
Your role is to decompose high-level goals into a structured plan and orchestrate Worker agents.

COGNITIVE RULES:
1. Always maintain the plan in a physical file (e.g., 'plan.json') in the workspace.
2. Use 'core.fs.write' to create or update the plan.
3. When dispatching tasks, use the 'context_pointer' to point to the plan file and specify the 'current_task'.
4. 'payload' should only contain transient execution data (like the action to spawn or a brief instruction).
5. 'context_pointer' should follow this structure: {"type": "plan", "uri": "plan.json", "current_task": "task_id"}

PLAN STRUCTURE (plan.json):
{
  "goal": "original goal",
  "tasks": [
    {"id": "task_1", "description": "...", "status": "pending/running/done", "result": "..."},
    ...
  ]
}
"""

WORKER_PROMPT = """You are an AegisOS Worker Agent.
Your role is to execute specific tasks assigned by the Coordinator.

COGNITIVE RULES:
1. You will receive a 'context_pointer' pointing to a 'plan.json' and a 'current_task' ID.
2. You MUST explicitly use 'core.fs.read' to load the task details or the plan from the provided URI.
3. Focus ONLY on the 'current_task' specified in the context_pointer.
4. When finished, use 'core.fs.write' to update the task status in 'plan.json' and INFORM the Coordinator.
5. 'payload' is for transient data; all persistent progress must be in the workspace.
"""

class CoordinatorAgent(AACPAgent):
    def __init__(self, llm_engine: BaseLLMEngine, **kwargs):
        kwargs.pop("role", None)
        super().__init__(
            role="coordinator",
            llm_engine=llm_engine,
            system_prompt=COORDINATOR_PROMPT,
            **kwargs
        )
        # Inherit skills from base (fs_read/write are already there)

class WorkerAgent(AACPAgent):
    def __init__(self, llm_engine: BaseLLMEngine, **kwargs):
        kwargs.pop("role", None)
        super().__init__(
            role="worker",
            llm_engine=llm_engine,
            system_prompt=WORKER_PROMPT,
            **kwargs
        )
        # Register specialized skills
        from aegisos.agents.skills.web_fetch import WebFetchSkill
        self.add_skill(WebFetchSkill())
