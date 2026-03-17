# Project Conventions

This document records the core architectural design, engineering practices, and development workflows of AegisOS, providing consistent guidance for the automated development of AI Agents.

## 1. Core Architecture and Tech Stack

- **Package Management**: Mandatory use of `uv`. All dependency additions must be through `uv add`.
- **Project Structure**: Follows the **Standard src-layout**.
  - `src/aegisos/`: Main source directory.
  - `tests/`: Unit test directory.
  - `scripts/`: E2E or tool scripts.
- **Programming Model**: **100% Asynchronous (async/await)**. All I/O, message dispatching, and Agent callbacks must be defined as `async def`.
- **Data Model**: Mandatory use of **Pydantic V2** (`BaseModel`, `ConfigDict`) for all AACP protocol and configuration definitions.
- **Path Safety**: All file system operations must pass `WorkspaceManager` Path Traversal validation.

## 2. Development Workflow

Follow this cycle for tasks in each Phase:

### 1. Research: Read project memory files to understand the current status and next tasks

- project-memory/vision.md
- project-memory/architecture.md
- project-memory/decisions.md
- project-memory/tasks.md

### 2. Plan: Clarify implementation details, interface definitions, and testing strategies

### 3. Act: Write/modify code

### 4. Validate

- Run targeted unit tests: `pytest tests/test_xxx.py`
- Run phase-specific E2E scripts: `python scripts/test_e2e_xxx.py`

### 5. Commit: Submit code and summarize the current Phase after verification

- commit message format: `feat(phaseX): description` or `fix(component): description`.

### 6. Update Project Memory

- Update task status in `tasks.md`.
- Record daily development progress in `changelog.md`.
- If there are new technical decisions, update `decisions.md`.
- Do not modify `vision.md` unless explicitly instructed.
- Do not modify `architecture.md` unless the architecture changes.

## 3. Module Responsibility Division

- `core.protocol`: Defines AACP communication protocol Standard Format and Agent URI specifications.
- `core.dispatcher`: Implements the message dispatch center based on `asyncio.Queue`, supporting local routing and remote Egress (Tailscale/Nostr, etc.).
- `core.workspace`: Manages secure file storage areas (Blackboard) with Session isolation.
- `core.llm`: LLM engine abstraction layer, supporting Structured Outputs.
- `agents/`: Stores implementation logic for various types of Agents.
- `memory/`: (To be developed) Handles Token routing interception and long/short-term memory.

## 4. Key Interface Conventions

- **Agent URI**: Format is `{id}@{instance}` (e.g., `assistant_123@local`). `BROADCAST` is a special reserved address.
- **AACP Message**: Contains `message_id`, `timestamp`, `sender`, `receiver`, `intent`, `payload`, `context_pointer`.
- **Agent Callback**: Suggested signature is `async def handle_message(self, message: AACPMessage) -> None`.
- **System Intents**:
  - `SPAWN`: Dynamically create new Agent instances.
  - `TERMINATE`: Destroy specified Agent instances.
- **Structured Thinking**: Agents use the `AACPResponse` model for internal reasoning, then convert to `AACPMessage` for dispatch.

---
*This document will be continuously updated as the project progresses.*

