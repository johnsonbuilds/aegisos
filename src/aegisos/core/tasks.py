from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    RETRYING = "retrying"

class Task(BaseModel):
    id: str
    description: str
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    role: Optional[str] = None
    assignee: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    revision: int = Field(default=0)

class Plan(BaseModel):
    goal: str
    tasks: List[Task] = Field(default_factory=list)
    revision: int = Field(default=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def get_task(self, task_id: str) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

class TaskUpdateProposal(BaseModel):
    """
    Proposed update from a Worker to the Coordinator.
    """
    task_id: str
    new_status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    expected_revision: Optional[int] = None

class TaskUpdateResult(BaseModel):
    """Deterministic outcome returned by Coordinator task-update handling."""
    ok: bool
    reason: Optional[str] = None

class PlanManager:
    """
    Deterministic management of plan.json.
    Enforces state machine and handles atomic persistence.
    """
    VALID_TRANSITIONS = {
        TaskStatus.PENDING: {TaskStatus.RUNNING, TaskStatus.FAILED},
        TaskStatus.RUNNING: {TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.RETRYING},
        TaskStatus.RETRYING: {TaskStatus.RUNNING, TaskStatus.FAILED},
        TaskStatus.DONE: set(),  # Final
        TaskStatus.FAILED: {TaskStatus.RETRYING},
    }

    def __init__(self, workspace: Any, filename: str = "plan.json"):
        self.workspace = workspace
        self.filename = filename

    async def load(self) -> Plan:
        """Load plan from workspace with validation."""
        try:
            content = await self.workspace.read_file(self.filename)
            return Plan.model_validate_json(content)
        except FileNotFoundError:
            # Return a blank plan if it doesn't exist yet
            return Plan(goal="N/A")
        except Exception as e:
            raise RuntimeError(f"Failed to load plan: {e}")

    async def save(self, plan: Plan):
        """Atomicsave to workspace."""
        await self.workspace.atomic_write(
            self.filename, 
            plan.model_dump_json(indent=2)
        )

    def propose_update(self, plan: Plan, proposal: TaskUpdateProposal) -> bool:
        """
        Apply a proposal with state machine and version (CAS) validation.
        """
        task = plan.get_task(proposal.task_id)
        if not task:
            return False
        
        # 1. Version Check (CAS)
        if proposal.expected_revision is None:
            return False
        # Skip check only when the caller explicitly requests bypass mode via -1.
        if proposal.expected_revision != -1 and task.revision != proposal.expected_revision:
            return False
            
        # 2. State Machine Check
        if proposal.new_status not in self.VALID_TRANSITIONS.get(task.status, set()):
            # If the transition is invalid, reject
            return False

        # 3. Apply Update
        task.status = proposal.new_status
        task.result = proposal.result
        task.error = proposal.error
        task.revision += 1
        plan.revision += 1
        return True
