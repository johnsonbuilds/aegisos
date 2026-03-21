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
- [x] **B1: Infinite Loop Guard**
    - [x] Add `max_steps` to every agent reasoning loop.
    - [x] Auto-terminate and persist loop diagnostics when the limit is exceeded.
- [ ] **B2: Retry / Exponential Backoff**
    - [ ] Add bounded retries for tool / network failures.
    - [ ] Persist final failures into workspace error logs.
- [ ] **B3: Termination Correctness**
    - [ ] Ensure `TASK_COMPLETE` deterministically triggers `TERMINATE`.
    - [ ] Verify dispatcher registry cleanup to prevent zombie agents.
- [ ] **B4: Task State Guard**
    - [x] Enforce task state machine: `pending -> doing -> done|failed`.
    - [x] Make Coordinator the single writer of `plan.json`.
    - [ ] Prevent redispatch of completed tasks.
    - [x] Add version / revision metadata and atomic plan updates.

### Task Group D: Minimal Safety (P1)
- [ ] **D1: Timeout / Kill Switch**
    - [x] Add task-level timeout.
    - [ ] Add tool-level timeout.
    - [x] Force failure + termination when timeout is exceeded.
- [ ] **D2: Sandbox Hardening (Minimal)**
    - [ ] Tighten resource limits for the current subprocess-based sandbox.
    - [ ] Clarify and enforce workspace-only access boundaries.
    - [ ] Keep scope minimal; do not claim final Zero-Trust completeness in this phase.

### Task Group A: Real Value Task Loops (P1, after P0 guardrails)

Goal: Validate that agents can produce outputs with potential economic value (not just execution correctness)

- [ ] **A2: Market Signal Monitor Loop** *(first stable loop)*
    - [ ]  Implement as a deterministic / functional monitoring path first.
    - [ ]  Integrate real data sources (e.g., prediction markets, crypto signals, trending topics).
    - [ ]  Output MUST include:
        - clear actionable decision (e.g., YES / NO / BUY / SELL)
        - reasoning (structured, not verbose noise)
        - confidence score (0~1)
    - [ ]  Run with bounded retries and bounded execution time.
    - [ ]  Pass 24h stability gate before the 72h validation run.
    - [ ]  Pass 72h validation without zombie agents, infinite retry, or duplicate dispatch.
- [ ] **A1: Actionable Intelligence Report Loop (upgraded from Daily Web Report)**
    - [ ]  Trigger once per day via scheduler tick -> Coordinator task materialization.
    - [ ]  Replace “information summary” with:
        - actionable insights
        - prioritized opportunities
        - recommended actions
    - [ ]  Persist `report.md` in workspace.
    - [ ]  Output must be:
        - decision-oriented (not descriptive)
        - structured (machine + human readable)
    - [ ]  Ensure no duplicate daily execution.

- [ ] **A0: Founder Daily Usage Loop**
    - [ ] Run at least one agent workflow daily for personal decision support
    - [ ] Log:
        - whether result was used
        - whether it influenced real decision
    - [ ] Track:
        - usefulness (yes/no)
        - trust level

- [ ] **A3: Paid Task Simulation Loop (🔥 Critical)**

> Goal: Simulate real marketplace tasks and validate agent output quality + evaluability

- Evaluation Schema (Required)

    - [ ] Define a strict evaluation schema for each task:
        - correctness (0/1 or score)
        - actionability (can user directly act?)
        - specificity (not generic)
        - consistency (same input → similar output)

    - [ ] Each output MUST be machine-evaluable (JSON-based scoring possible)
    ---

 - Requirements

    - [ ]  Define at least 3 task templates with:
        - clear objective
        - clear evaluation criteria
        - bounded scope

    ---

- Example Task Template

    ```
    Task:
    Identify a short-term opportunity in a prediction market within 24h

    Output must include:
    - explicit position (YES / NO)
    - reasoning
    - confidence score
    ```

    ---

- Execution Requirements

    - [ ]  Task must produce:
        - deterministic structure (JSON or strict markdown)
        - evaluable output (not vague text)
    - [ ]  Persist result in workspace
    - [ ]  Ensure repeatability across runs

    ---

- Validation Criteria

    - [ ]  Output is:
        - actionable
        - comparable (can be judged by another agent)
        - non-trivial (not generic summary)
    - [ ]  At least one task can run end-to-end without manual intervention



## Phase 2 Gates
- [ ] **Gate 1: Runtime Ready**
    - [x] C1
    - [x] C2
    - [x] B1
    - [ ] B3
    - [ ] B4
    - [ ] D1

## Gate 2: First Stable Real Loop

- [ ]  A2 completes 24h stable run
- [ ]  A3 produces evaluable outputs

---

## Gate 3: 72h Validation

- [ ]  At least one real value loop runs for 72h
- [ ]  No zombie agents
- [ ]  No duplicate task execution
- [ ]  No unexplained crash

---
*Note: For long-term sequencing, please see [Roadmap](./roadmap.md)*
