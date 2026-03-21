import json
import logging
from pathlib import Path
from typing import Optional, Any, Dict
from aegisos.agents.base import AACPAgent
from aegisos.core.llm import BaseLLMEngine
from aegisos.core.actions import AACPAction
from aegisos.core.protocol import AACPMessage, AACPIntent

logger = logging.getLogger("CommonAgents")

COORDINATOR_PROMPT = """You are the AegisOS Coordinator. 
Your role is to decompose high-level goals into a structured plan and orchestrate Worker agents.

COGNITIVE RULES (STRATEGIC SEQUENCE):
1. INITIALIZE: Your VERY FIRST action after receiving a new goal MUST be creating 'plan.json' using 'core.fs.write'. 
   Populate it with the ACTUAL user goal and a list of sequential tasks.
2. TASK UPDATE: When a Worker INFORMs you of a result, you MUST:
    a. 'core.fs.read' the 'plan.json' to get the current state and revision.
   b. Update the task status to 'done' or 'failed' and include the result/pointer.
    c. 'core.fs.write' the updated plan back to 'plan.json'.
3. SINGLE WRITER: You are the SOLE WRITER of 'plan.json'. Never let Workers modify it.
4. DYNAMIC SPAWNING: If a task requires a role not yet present, use 'SPAWN' to 'system@local'.
5. TASK DISPATCH: Use 'context_pointer' to 'plan.json' when sending 'REQUEST' to Workers.
6. Do NOT place task descriptions or plan content into `payload`. If runtime parameters are needed (for example `input_context_pointer` or `output_path`), keep them minimal and let the Worker read `plan.json` for task details.

PLAN STRUCTURE (plan.json):
{
  "goal": "original goal",
  "revision": 1,
  "tasks": [
    {"id": "task_1", "description": "...", "status": "pending/running/done/failed", "assignee": "agent_id_if_known", "role": "required_role", "result": "..."}
  ]
}

DYNAMIC AGENT SPAWNING:
1. SPAWN message to 'system@local' with payload: {"agent_type": "worker", "role": "web_scraper"}.
2. When you receive status "SPAWNED" with an "agent_id", that worker is READY. Do not spawn it again.
3. Use the specific "agent_id" (e.g. worker_abcd@local-node) for all subsequent REQUESTs.
"""

WORKER_PROMPT = """You are an AegisOS Worker Agent.
Your role is to execute specific tasks assigned by the Coordinator.

COGNITIVE RULES (EXECUTION):
1. READ PLAN: Use 'core.fs.read' to load 'plan.json' and inspect the `current_task` from `context_pointer` before deciding how to execute.
2. TRUST THE REQUEST: If the Coordinator sends you a `REQUEST` with a valid `current_task`, that request authorizes execution even when the task assignee in `plan.json` is a logical alias such as `analyst@local`.
3. EXECUTE: Use ONLY the exact skill names listed in AVAILABLE SKILLS (for example `core.cog.web_fetch`, `core.fs.read`, `core.fs.write`). Never invent new action names.
4. SELF-ACTION: When using a skill, set 'receiver' to your own URI (or null) to trigger the action.
5. If `payload.input_context_pointer` is provided, treat it only as a runtime artifact hint; still read `plan.json` for authoritative task details.
6. If `payload.output_path` is provided, treat it only as a runtime output target; it does not replace reading the task definition from `plan.json`.
7. REPORT: Once the task is complete, send an 'INFORM' to the Coordinator with the result, including any saved artifact path.
8. CAS metadata (`task_id`, `expected_revision`) will be attached automatically from the task context. Focus on correct execution and clear results.
"""

from aegisos.core.tasks import Plan, PlanManager, Task, TaskUpdateProposal, TaskUpdateResult, TaskStatus

class CoordinatorAgent(AACPAgent):
    MAX_TASK_INPUT_CHARS = 20000
    ROLE_TARGETS = {
        "web_scraper": ["web_scraper@local"],
        "analyst": ["analyst@local", "report_generator@local"],
        "summarizer": ["summarizer@local", "analyst@local", "report_generator@local"],
        "report_generator": ["report_generator@local", "analyst@local"],
    }

    def __init__(self, llm_engine: BaseLLMEngine, **kwargs):
        kwargs.pop("role", None)
        super().__init__(
            role="coordinator",
            llm_engine=llm_engine,
            system_prompt=COORDINATOR_PROMPT,
            **kwargs
        )
        self.plan_manager = PlanManager(self.workspace, filename="plan.json") if self.workspace else None

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
            expected_revision = self._parse_expected_revision(payload.get("expected_revision"))
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
                if proposal.new_status == TaskStatus.DONE:
                    await self._dispatch_next_pending_task(plan)
                logger.info(f"[{self.agent_id}] Successfully updated task {proposal.task_id} to {proposal.new_status}")
                return TaskUpdateResult(ok=True)
            else:
                logger.warning(f"[{self.agent_id}] Rejected task update for {proposal.task_id}: CAS or Transition failure.")
                return TaskUpdateResult(ok=False, reason="cas_or_transition_failure")
        except Exception as e:
            logger.error(f"[{self.agent_id}] Failed to process task update: {e}")
            return TaskUpdateResult(ok=False, reason="task_update_exception")

    @staticmethod
    def _parse_expected_revision(value: Any) -> Optional[int]:
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            normalized = value.strip()
            if normalized == "-1":
                return -1
            if normalized.isdigit():
                return int(normalized)
        return None

    async def _augment_outgoing_payload(self, payload: Dict[str, Any], response, target_uri: str) -> Dict[str, Any]:
        payload = await super()._augment_outgoing_payload(payload, response, target_uri)
        if response.intent != AACPIntent.REQUEST or target_uri in {"system@local", self.dispatcher.SYSTEM_AGENT_ID if self.dispatcher else None}:
            return payload
        if not self.plan_manager:
            return payload

        try:
            plan = await self.plan_manager.load()
            current_task = response.context_pointer.get("current_task") if isinstance(response.context_pointer, dict) else None
            task = self._select_task_for_dispatch(plan, target_uri, current_task=current_task)
            if not task:
                return payload

            payload.pop("action", None)
            payload.pop("task_description", None)
            payload.pop("task_role", None)

            input_pointer = self._find_latest_context_pointer(plan, task.id)
            if input_pointer:
                payload.setdefault("input_context_pointer", await self._prepare_task_input(input_pointer))

            output_path = self._default_output_path(task)
            if output_path:
                payload.setdefault("output_path", output_path)
        except Exception as exc:
            logger.warning(f"[{self.agent_id}] Failed to normalize outgoing task payload: {exc}")

        return payload

    async def _augment_outgoing_context_pointer(
        self,
        context_pointer: Optional[Dict[str, Any] | str],
        response,
        target_uri: str,
    ) -> Optional[Dict[str, Any] | str]:
        context_pointer = await super()._augment_outgoing_context_pointer(context_pointer, response, target_uri)
        if response.intent != AACPIntent.REQUEST or not self.plan_manager:
            return context_pointer

        try:
            plan = await self.plan_manager.load()
            current_task = context_pointer.get("current_task") if isinstance(context_pointer, dict) else None
            task = self._select_task_for_dispatch(plan, target_uri, current_task=current_task)
            if not task:
                return context_pointer

            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.RUNNING
                task.assignee = target_uri
                plan.revision += 1
                await self.plan_manager.save(plan)
            elif not task.assignee:
                task.assignee = target_uri
                plan.revision += 1
                await self.plan_manager.save(plan)

            return {
                "type": "plan",
                "uri": self.plan_manager.filename,
                "current_task": task.id,
                "expected_revision": task.revision,
            }
        except Exception as exc:
            logger.warning(f"[{self.agent_id}] Failed to enrich task context pointer: {exc}")
            return context_pointer

    async def _dispatch_next_pending_task(self, plan: Plan) -> bool:
        if not self.dispatcher or not self.plan_manager:
            return False

        next_task = next((task for task in plan.tasks if task.status == TaskStatus.PENDING), None)
        if not next_task:
            return False

        receiver = self._resolve_task_receiver(next_task)
        if not receiver:
            logger.warning(f"[{self.agent_id}] No available receiver found for task role '{next_task.role}'.")
            return False

        next_task.status = TaskStatus.RUNNING
        next_task.assignee = receiver
        plan.revision += 1
        await self.plan_manager.save(plan)

        payload = {
        }

        input_pointer = self._find_latest_context_pointer(plan, next_task.id)
        if input_pointer:
            payload["input_context_pointer"] = await self._prepare_task_input(input_pointer)

        output_path = self._default_output_path(next_task)
        if output_path:
            payload["output_path"] = output_path

        await self.dispatcher.send_message(
            AACPMessage(
                sender=self.agent_id,
                receiver=receiver,
                intent=AACPIntent.REQUEST,
                payload=payload,
                context_pointer={
                    "type": "plan",
                    "uri": self.plan_manager.filename,
                    "current_task": next_task.id,
                    "expected_revision": next_task.revision,
                },
            )
        )
        logger.info(f"[{self.agent_id}] Dispatched next task {next_task.id} to {receiver}")
        return True

    def _resolve_task_receiver(self, task: Task) -> Optional[str]:
        if not self.dispatcher:
            return task.assignee

        candidates = []
        if task.assignee:
            candidates.append(task.assignee)
        if task.role:
            candidates.extend(self.ROLE_TARGETS.get(task.role, []))
            candidates.append(f"{task.role}@local")

        seen = set()
        for candidate in candidates:
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)
            resolved = self.dispatcher.resolve_target(candidate) if hasattr(self.dispatcher, "resolve_target") else candidate
            if candidate in getattr(self.dispatcher, "agents", {}) or resolved in getattr(self.dispatcher, "agents", {}):
                return candidate

        return None

    def _select_task_for_dispatch(self, plan: Plan, target_uri: str, current_task: Optional[str] = None) -> Optional[Task]:
        if current_task:
            task = plan.get_task(current_task)
            if task:
                return task

        for task in plan.tasks:
            if task.status == TaskStatus.RUNNING and task.assignee == target_uri:
                return task

        for task in plan.tasks:
            if task.status == TaskStatus.PENDING:
                return task

        return None

    def _find_latest_context_pointer(self, plan: Plan, current_task_id: str) -> Optional[str]:
        for task in reversed(plan.tasks):
            if task.id == current_task_id:
                continue
            if task.status != TaskStatus.DONE or not isinstance(task.result, dict):
                continue
            pointer = task.result.get("context_pointer") or task.result.get("report_path")
            if isinstance(pointer, str):
                return pointer
        return None

    def _default_output_path(self, task: Task) -> Optional[str]:
        description = task.description.lower()
        if "summary" in description or "report" in description or task.role in {"analyst", "report_generator"}:
            return "indiehackers_summary.txt"
        return None

    async def _prepare_task_input(self, input_pointer: str) -> str:
        if not self.workspace:
            return input_pointer

        try:
            content = await self.workspace.read_file(input_pointer)
        except Exception:
            return input_pointer

        if len(content) <= self.MAX_TASK_INPUT_CHARS:
            return input_pointer

        excerpt_name = Path(input_pointer).stem + "_excerpt.txt"
        excerpt_path = f"artifacts/{excerpt_name}"
        excerpt_content = content[: self.MAX_TASK_INPUT_CHARS] + "\n\n...[truncated by coordinator for prompt safety]"
        await self.workspace.write_file(excerpt_path, excerpt_content)
        return excerpt_path

class WorkerAgent(AACPAgent):
    MAX_DIRECT_TASK_INPUT_CHARS = 12000

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

    async def handle_message(self, message: AACPMessage):
        if await self._maybe_execute_artifact_task(message):
            return
        await super().handle_message(message)

    async def _maybe_execute_artifact_task(self, message: AACPMessage) -> bool:
        if message.intent != AACPIntent.REQUEST or not self.workspace or not self.dispatcher:
            return False
        if not isinstance(message.payload, dict) or not isinstance(message.context_pointer, dict):
            return False

        current_task = message.context_pointer.get("current_task")
        plan_uri = message.context_pointer.get("uri")
        input_pointer = message.payload.get("input_context_pointer")
        output_path = message.payload.get("output_path")
        if not isinstance(current_task, str) or not isinstance(plan_uri, str):
            return False
        if not isinstance(input_pointer, str) or not isinstance(output_path, str):
            return False

        try:
            plan = Plan.model_validate_json(await self.workspace.read_file(plan_uri))
            task = plan.get_task(current_task)
            if not task or not self._is_direct_artifact_task(task):
                return False

            source_text = await self.workspace.read_file(input_pointer)
            excerpt = source_text[: self.MAX_DIRECT_TASK_INPUT_CHARS]
            if len(source_text) > self.MAX_DIRECT_TASK_INPUT_CHARS:
                excerpt += "\n\n...[truncated for direct task execution]"

            summary = await self.llm.generate(
                messages=[
                    {
                        "role": "system",
                        "content": "You produce concise plain-text reports from provided workspace artifacts. Return only the final report text.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Task ID: {task.id}\n"
                            f"Task Description: {task.description}\n"
                            f"Source Artifact: {input_pointer}\n"
                            "Write a short plain-text report with a title, 3-6 key points, and a brief conclusion.\n\n"
                            f"Source Content:\n{excerpt}"
                        ),
                    },
                ]
            )

            if not isinstance(summary, str):
                summary = json.dumps(summary, ensure_ascii=False) if isinstance(summary, (dict, list)) else str(summary)

            await self.workspace.write_file(output_path, summary)

            await self.dispatcher.send_message(
                AACPMessage(
                    sender=self.agent_id,
                    receiver=message.sender,
                    intent=AACPIntent.INFORM,
                    payload={
                        "task_id": task.id,
                        "expected_revision": message.context_pointer.get("expected_revision"),
                        "status": TaskStatus.DONE.value,
                        "report_path": output_path,
                        "result": {
                            "message": f"Generated report at {output_path}",
                            "context_pointer": output_path,
                            "report_path": output_path,
                            "source_context_pointer": input_pointer,
                            "artifact_path": output_path,
                        },
                    },
                    context_pointer=message.context_pointer,
                )
            )
            return True
        except Exception as exc:
            await self.dispatcher.send_message(
                AACPMessage(
                    sender=self.agent_id,
                    receiver=message.sender,
                    intent=AACPIntent.INFORM,
                    payload={
                        "task_id": current_task,
                        "expected_revision": message.context_pointer.get("expected_revision"),
                        "status": TaskStatus.FAILED.value,
                        "error": str(exc),
                    },
                    context_pointer=message.context_pointer,
                )
            )
            return True

    @staticmethod
    def _is_direct_artifact_task(task: Task) -> bool:
        if task.role in {"analyst", "summarizer", "report_generator"}:
            return True
        description = task.description.lower()
        return any(keyword in description for keyword in ["summary", "report", "analyze", "analysis"])

    async def _augment_outgoing_payload(self, payload: Dict[str, Any], response, target_uri: str) -> Dict[str, Any]:
        payload = await super()._augment_outgoing_payload(payload, response, target_uri)
        task_context = self._last_context_pointer if isinstance(self._last_context_pointer, dict) else None
        if not task_context or target_uri == self.agent_id:
            return payload

        if response.intent not in {AACPIntent.INFORM, AACPIntent.TASK_COMPLETE, AACPIntent.ERROR}:
            return payload

        current_task = task_context.get("current_task")
        if current_task and "task_id" not in payload:
            payload["task_id"] = current_task

        expected_revision = task_context.get("expected_revision")
        if expected_revision is not None and "expected_revision" not in payload:
            payload["expected_revision"] = expected_revision

        if response.intent == AACPIntent.ERROR:
            payload.setdefault("status", TaskStatus.FAILED.value)
        else:
            payload.setdefault("status", TaskStatus.DONE.value)

        result_value = payload.get("result")
        if isinstance(result_value, str):
            result_block: Dict[str, Any] = {"message": result_value}
        elif isinstance(result_value, dict):
            result_block = result_value.copy()
        else:
            result_block = {}

        if isinstance(self._last_action_result, dict):
            for key in ["context_pointer", "source_context_pointer", "artifact_path", "message", "url", "status_code", "path"]:
                if key in self._last_action_result and key not in result_block:
                    result_block[key] = self._last_action_result[key]

        if "report_path" in payload and "report_path" not in result_block:
            result_block["report_path"] = payload["report_path"]

        if result_block:
            payload["result"] = result_block

        return payload
