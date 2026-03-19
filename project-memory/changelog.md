# AegisOS Changelog

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
- **WebScraper Skill**: Implemented `WebScraperSkill` (using `httpx`) as an external plugin, decoupling it from the core protocol.
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
