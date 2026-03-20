# AegisOS Active Tasks (Current Phase: Phase 2)

**Responsibility**
- Defines concrete, executable tasks that realize roadmap capabilities.
- Answers what to do next and how to move the system forward.

## Recent Review (Completed Baseline)
- [x] **Core Kernel Implementation**: Dispatcher, Workspace, Protocol, and Kernel Agent are online.
- [x] **Security and Stability Foundations**: Completed edge case unit tests and released the AACP protocol specification document.
- [x] **Single-Node MVP Baseline**:
    - [x] Coordinator/Worker collaboration loop validated.
    - [x] Real web capability integrated via `WebScraperSkill` / `WebFetchSkill`.
    - [x] Workspace-based task flow validated with `context_pointer`.
    - [x] End-to-end demo provided in `examples/fetch_and_report.py`.

## Current Focus (Phase 2: System Validation & Runtime Guardrails)

### Task Group C: Observability First (P0)
- [x] **C1: Message Trace Log**
    - [x] Record `message_id`, `timestamp`, `sender`, `receiver`, and `intent` for every AACP message.
    - [x] Attach runtime-level tracing metadata (`session_id`, `task_id`, optional `parent_message_id`) without bloating the AACP protocol.
    - [x] Support querying logs by `session_id`.
- [x] **C2: Task Timeline**
    - [x] Record lifecycle events: `TASK_CREATED`, `SPAWN_REQUESTED`, `SPAWNED`, `STARTED`, `ACTION_FINISHED`, `TASK_COMPLETE`, `TERMINATE_REQUESTED`, `TERMINATED`.
    - [x] Make stalled phases diagnosable from timeline logs.
    - [x] Enable replay-oriented inspection for long-running sessions.
- [ ] **C3: Workspace Audit Log**
    - [ ] Record every workspace write with `agent_id`, `task_id`, `session_id`, file path, and timestamp.
    - [ ] Establish write-level provenance first; full file diffing is a follow-up enhancement.

### Task Group B: Runtime Guardrails (P0)
- [ ] **B1: Infinite Loop Guard**
    - [ ] Add `max_steps` to every agent reasoning loop.
    - [ ] Auto-terminate and persist loop diagnostics when the limit is exceeded.
- [ ] **B2: Retry / Exponential Backoff**
    - [ ] Add bounded retries for tool / network failures.
    - [ ] Persist final failures into workspace error logs.
- [ ] **B3: Termination Correctness**
    - [ ] Ensure `TASK_COMPLETE` deterministically triggers `TERMINATE`.
    - [ ] Verify dispatcher registry cleanup to prevent zombie agents.
- [ ] **B4: Task State Guard**
    - [ ] Enforce task state machine: `pending -> doing -> done|failed`.
    - [ ] Make Coordinator the single writer of `plan.json`.
    - [ ] Prevent redispatch of completed tasks.
    - [ ] Add version / revision metadata and atomic plan updates.

### Task Group D: Minimal Safety (P1)
- [ ] **D1: Timeout / Kill Switch**
    - [ ] Add task-level timeout.
    - [ ] Add tool-level timeout.
    - [ ] Force failure + termination when timeout is exceeded.
- [ ] **D2: Sandbox Hardening (Minimal)**
    - [ ] Tighten resource limits for the current subprocess-based sandbox.
    - [ ] Clarify and enforce workspace-only access boundaries.
    - [ ] Keep scope minimal; do not claim final Zero-Trust completeness in this phase.

### Task Group A: Real Task Loops (P1, after P0 guardrails)
- [ ] **A2: API Monitor Loop** *(first stable loop)*
    - [ ] Implement as a deterministic / functional monitoring path first.
    - [ ] Run with bounded retries and bounded execution time.
    - [ ] Pass 24h stability gate before the 72h validation run.
    - [ ] Pass 72h validation without zombie agents, infinite retry, or duplicate dispatch.
- [ ] **A1: Daily Web Report Loop**
    - [ ] Trigger once per day via scheduler tick -> Coordinator task materialization.
    - [ ] Persist `report.md` in workspace without duplicate daily execution.
- [ ] **A3: Daily Content Generation Loop**
    - [ ] Trigger once per day via scheduler tick -> Coordinator task materialization.
    - [ ] Persist `post.txt` with stable structure and no duplicate window execution.

### Deferred Track (After Phase 2 Stabilizes)
- [ ] **Prompt Optimization**: Improve `AACPResponse` stability across models.
- [ ] **Prompt Caching**: Reduce repetitive prompt cost after runtime becomes stable.
- [ ] **Memory Engine Expansion**:
    - [ ] Token-aware hot memory truncation.
    - [ ] Cold memory / vector store integration.
    - [ ] Knowledge distillation background flow.
- [ ] **HITL Interceptor**: Define approval workflows for sensitive actions.

## Phase 2 Gates
- [ ] **Gate 1: Runtime Ready**
    - [x] C1
    - [x] C2
    - [ ] B1
    - [ ] B3
    - [ ] B4
    - [ ] D1
- [ ] **Gate 2: First Stable Real Loop**
    - [ ] A2 completes 24h stable run.
- [ ] **Gate 3: 72h Validation**
    - [ ] At least one real loop runs for 72h.
    - [ ] No zombie agents.
    - [ ] No duplicate task execution.
    - [ ] No unexplained crash.

---
*Note: For long-term sequencing, please see [Roadmap](./roadmap.md)*
