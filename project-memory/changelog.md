# AegisOS Changelog

## [0.1.7] - 2026-03-20
### Added
- **Plan Guard Module**: Added `src/aegisos/core/tasks.py` with `Plan`, `Task`, `TaskUpdateProposal`, and deterministic Coordinator update outcomes.
- **Guardrail Regression Tests**: Added focused tests for Coordinator deterministic updates, missing `expected_revision` rejection, dispatcher timeout cleanup, and agent self-unregister on step exhaustion.

### Changed
- **Configuration Loading**: `AegisConfig` now supports `aegisos.json` plus environment overrides for `agent_max_steps` and `task_timeout`.
- **Coordinator Determinism**: `CoordinatorAgent` now handles Worker task-update `INFORM` messages without falling back to the LLM path and requires `expected_revision` for CAS-safe plan updates.
- **Agent Lifecycle Guard**: `AACPAgent` now enforces `max_steps`, ignores new messages after shutdown, and unregisters itself from the dispatcher when the loop guard trips.
- **Dispatcher Kill Switch**: `AegisDispatcher` now enforces task-level timeouts, unregisters timed-out agents, raises `AgentExecutionTimeout`, and preserves safe queue shutdown semantics while broadcasts collect timeout failures.
- **Workspace Atomic Writes**: `WorkspaceManager` now persists `plan.json` via tmp-then-replace atomic writes to prevent partial corruption during concurrent task-state updates.

## [0.1.6] - 2026-03-20
### Added
- **Dispatcher Trace Log**: Added workspace-backed JSONL message tracing at `logs/message_trace.jsonl`, including delivery outcomes and runtime metadata such as `session_id` and `task_id`.
- **Task Timeline Log**: Added workspace-backed JSONL lifecycle logging at `logs/task_timeline.jsonl`, covering task dispatch, execution, spawn, and termination events.

### Changed
- **Phase Rebaseline**: Promoted **System Validation & Runtime Guardrails** to the new Phase 2 after the single-node MVP baseline was proven.
- **Roadmap Reshaping**: Archived the first real task loop as a completed bridge milestone and deferred cognition-efficiency work until after runtime stability.
- **Execution Priorities**: Declared observability, loop guards, termination correctness, task-state safety, and timeout control as the Phase 2 entry gate for real-world validation.
- **WorkspaceManager**: Added append support so runtime logs can be persisted through the same path-safe async file API.
- **Dispatcher Shutdown**: Waits for queued messages to drain before stopping, preventing in-flight trace loss.
- **Dispatcher Observability**: Centralized task lifecycle event capture in the dispatcher to support replay and debugging without extending the AACP protocol.

## [0.1.5] - 2026-03-19
### Changed
- **Cognitive Architecture Mapping**: Strictly separated transient execution (`payload`) from persistent cognition (`context_pointer`).
- **AACP Message Refactor**: Supported structured `context_pointer` with `uri`, `type`, and `current_task`.
- **AACPAgent Intelligence**: Enhanced **Cognitive Indexing**; agents now receive structured `context_pointer` and must explicitly read workspace state using skills (maintaining Zero-Trust Cognition).
- **Common Agents Refactor**: Removed hardcoded loops in `CoordinatorAgent` and `WorkerAgent`, migrating them to a "Blackboard" system using LLM-driven planning.
- **Architectural Refinement**: Formalized the responsibility boundary between `payload` (Execution Layer) and `context_pointer` (Cognitive Layer).

## [0.1.4] - 2026-03-17
### Added
- **Pluggable Skills**: Introduced `BaseSkill` and a dynamic skill registry in `AACPAgent`.
- **WebFetch Architecture Refactor**:
  - Implemented `BaseFetchEngine` for decoupling fetch logic from skill execution.
  - Added `SimpleHttpEngine` as the default pluggable engine.
  - Enhanced `WebFetchSkill` to support workspace persistence, ensuring large payloads don't clog the AACP bus.
  - Migrated HTML-to-Markdown conversion to the unified `WebFetchSkill`.
  - Updated `WorkerAgent` to use the new `WebFetchSkill` via capability injection.
- **Common Agents**: Added `CoordinatorAgent` and `WorkerAgent` for standard task orchestration.
- **SandboxRunner**: Completed the initial `SandboxRunner` based on restricted subprocesses.
- **Task 8 Demo**: Created `examples/fetch_and_report.py` to demonstrate the full agent collaboration loop.

### Changed
- **Agent Factory**: Updated `AgentFactory` to support lazy loading of common agent types.
- **Dispatcher**: Enhanced the `SPAWN` logic to automatically inject the default LLM engine for known agent types.
- **AACPAgent**: Generalized the self-execution (Reflexion) loop to support both built-in actions and registered skills.

## [0.1.3] - 2026-03-16
### Added
- **Standard Actions**: Introduced `src/aegisos/core/actions.py`, defining the standard action enum `AACPAction` (e.g., `core.exec.code`, `core.fs.read`, etc.).
- **Action Payload Schema**: Introduced the Pydantic validation base class `ActionPayload` for standard actions.

### Changed
- **AACP Protocol Refactor**: 
    - Removed unreasonable `CODE_EXEC` and `CODE_RESULT` from `AACPIntent`.
    - Adhered to the principle of "decoupling protocol primitives from business payloads."
- **AACPAgent Intelligence Upgrade**: 
    - `AACPResponse` now supports the `action` field.
    - Implemented an automatic injection mechanism from `action` to `payload["action"]`.
    - Refactored `Reflexion` logic to be triggered based on standard `REQUEST` + `AACPAction.CODE_EXEC`.

## [0.1.2] - 2026-03-13
### Added
- **Dynamic Spawning**: `AegisDispatcher` (system@local) now supports dynamic instantiation of `AACPAgent` via the `SPAWN` intent.
- **Lifecycle Integration**: Implemented the complete agent lifecycle loop: "SPAWN -> WORK -> TERMINATE".
- **NOOP Mechanism**: Introduced an optional `receiver` mechanism in `AACPResponse`, allowing Agents to break infinite loops by not sending messages.
- **Integration Tests**: Added `tests/test_aacp_integration.py` to verify multi-agent dynamic collaboration workflows.

### Changed
- **AACPAgent Refactor**: Optimized the `__init__` signature to support automatic URI generation based on roles and UUIDs.
- **Auto-Reaction**: `AACPAgent` now automatically triggers a thinking action via `handle_message` after receiving a message.

## [0.1.1] - 2026-03-13

### Fixed
- Fixed system proxy protection logic in `Dispatcher` during registration/unregistration.
- Fixed automatic creation logic in `WorkspaceManager` when handling deep directories.
