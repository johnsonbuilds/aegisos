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

COGNITIVE RULES (SINGLE WRITER PRINCIPLE):
1. You are the SOLE WRITER of 'plan.json' in the workspace.
2. Use 'core.fs.write' to create or update the plan.
3. When dispatching tasks, use the 'context_pointer' to point to the plan file and specify the 'current_task'.
4. 'context_pointer' structure: {"type": "plan", "uri": "plan.json", "current_task": "task_id"}
5. Monitor task status: pending -> running -> done|failed.
6. When a Worker INFORMs you of task completion, you MUST read 'plan.json', update the status/result, and save it.

PLAN STRUCTURE (plan.json):
{
  "goal": "original goal",
  "revision": 1,
  "tasks": [
    {"id": "task_1", "description": "...", "status": "pending/running/done/failed", "assignee": "worker_id", "result": "..."}
  ]
}
"""

WORKER_PROMPT = """You are an AegisOS Worker Agent.
Your role is to execute specific tasks assigned by the Coordinator.

COGNITIVE RULES (READ-ONLY ACCESS):
1. You MUST NOT modify 'plan.json' directly. You have READ-ONLY access to the plan.
2. You will receive a 'context_pointer' pointing to 'plan.json' and a 'current_task' ID.
3. Use 'core.fs.read' to load task details from the plan file.
4. Execute the 'current_task' logic using available skills (e.g., web_fetch).
5. When finished, INFORM the Coordinator (sender of the task) of the outcome (success/failure, result data).
6. Your INFORM payload MUST include 'expected_revision', which is the task revision you observed when reading the plan.
7. Provide clear, structured results in your INFORM payload so the Coordinator can update the plan.
"""

from aegisos.core.tasks import PlanManager, TaskUpdateProposal, TaskUpdateResult, TaskStatus

class CoordinatorAgent(AACPAgent):
    def __init__(self, llm_engine: BaseLLMEngine, **kwargs):
        kwargs.pop("role", None)
        super().__init__(
            role="coordinator",
            llm_engine=llm_engine,
            system_prompt=COORDINATOR_PROMPT,
            **kwargs
        )
        self.plan_manager = PlanManager(self.workspace) if self.workspace else None

    async def handle_message(self, message: AACPMessage):
        """
        Extended handle_message for Coordinator: 
        Automatically process task updates from Workers if possible.
        """
        # 1. Deterministic Logic: task updates must never fall back to the LLM path.
        if message.intent == AACPIntent.INFORM and "task_id" in message.payload:
            outcome = await self._process_task_update(message)
            if outcome.ok:
                logger.debug(f"[{self.agent_id}] Deterministic update successful. Bypassing LLM.")
            else:
                logger.warning(f"[{self.agent_id}] Deterministic task update rejected: {outcome.reason}")
                if self.dispatcher:
                    await self.dispatcher.send_message(AACPMessage(
                        sender=self.agent_id,
                        receiver=message.sender,
                        intent=AACPIntent.ERROR,
                        payload={
                            "task_id": message.payload.get("task_id"),
                            "reason": outcome.reason,
                        }
                    ))
            return
            
        # 2. Proceed to standard LLM reasoning (think)
        await super().handle_message(message)

    async def _process_task_update(self, message: AACPMessage) -> TaskUpdateResult:
        """
        Internal deterministic logic to update plan.json based on Worker feedback.
        Returns a structured outcome for deterministic handling.
        """
        if not self.plan_manager:
            return TaskUpdateResult(ok=False, reason="plan_manager_unavailable")

        try:
            payload = message.payload
            expected_revision = payload.get("expected_revision")
            if expected_revision is None:
                return TaskUpdateResult(ok=False, reason="missing_expected_revision")

            proposal = TaskUpdateProposal(
                task_id=payload["task_id"],
                new_status=payload.get("status", TaskStatus.DONE),
                result=payload.get("result"),
                error=payload.get("error"),
                expected_revision=expected_revision
            )
            
            plan = await self.plan_manager.load()
            if self.plan_manager.propose_update(plan, proposal):
                await self.plan_manager.save(plan)
                logger.info(f"[{self.agent_id}] Successfully updated task {proposal.task_id} to {proposal.new_status}")
                return TaskUpdateResult(ok=True)
            else:
                logger.warning(f"[{self.agent_id}] Rejected task update for {proposal.task_id}: CAS or Transition failure.")
                return TaskUpdateResult(ok=False, reason="cas_or_transition_failure")
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to process task update: {e}")
            return TaskUpdateResult(ok=False, reason="task_update_exception")

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
