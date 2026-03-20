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

## 2. Development Task Workflow

If it is a development task ,Follow below steps:

### 1. Research: Read project memory files to understand the current status and next tasks

- project-memory/vision.md
- project-memory/architecture.md
- project-memory/decisions.md
- project-memory/tasks.md

### 2. Plan: Clarify implementation details, interface definitions, and testing strategies

- **Critical Review (MANDATORY)**: Upon receiving any task or requirement, **ASSUME it may have issues**. Critically analyze the request for architectural conflicts , implementation inconsistencies, or ambiguities.
- **Challenge & Clarify**: **YOU MUST** explicitly raise any reasonable doubts or questions to the human developer. **DO NOT** begin coding until all critical points are clarified and confirmed.
- **Constraint**: Must strictly adhere to the design principles and technical decisions defined in `project-memory/architecture.md` and `project-memory/decisions.md`.

### 3. Act: Write/modify code

- **Constraint**: Ensure implementation is consistent with the planned strategy and aligns with the existing architecture and project decisions.
- **Surgical Edits**: Use `replace` for precise edits and `write_file` only for new files.

### 4. Validate & Review

- **Validation**: Run targeted unit tests (`pytest tests/test_xxx.py`) and phase-specific E2E scripts.
- **Code Review (MANDATORY)**: After implementation and testing, present the changes as a **Review Request**. Briefly explain the technical rationale.
- **Approval Gate**: **STOP and WAIT** for the human developer to say "Review Approved". Do not proceed to final updates or commits without explicit approval.

### 5. Commit: Submit code and summarize the current Phase after verification

- commit message format: `feat(phaseX): description` or `fix(component): description`.

### 6. Update Project Memory

- Update task status in `tasks.md`.
- Record daily development progress in `changelog.md`.
- If there are new technical decisions, update `decisions.md`.
- Do not modify `vision.md` and `roadmap.md` unless explicitly instructed.
- Do not modify `architecture.md` unless the architecture changes.

## 3. Code Review Task Workflow

If it is a code review task, Follow below priciples:

### 1. Context Acquisition

- Read relevant project memory:
    - `architecture.md`
    - `decisions.md`
- Read the target code / diff carefully

---

### 2. Critical Analysis (MANDATORY)

The Review Agent MUST assume the implementation may contain flaws.

Focus on:

- **Architecture Violations**
    - Does it break layering / module boundaries?
- **Consistency Issues**
    - Naming, async model, protocol usage
- **Correctness Risks**
    - Edge cases, race conditions, retries, loop guards
- **Scalability Risks**
    - Will this break under long-running agents?
- **Security Risks**
    - Workspace path safety, injection surfaces
- **AegisOS-specific invariants**
    - message flow correctness
    - agent lifecycle correctness

---

### 3. Issue Classification

All findings must be categorized:

- 🔴 Critical (must fix before merge)
- 🟠 Major (should fix)
- 🟡 Minor (optional improvements)

---

### 4. Review Output Format (STRICT)

example output:

```
## Review Summary

### Critical Issues

### Major Issues

### Minor Suggestions

### Final Verdict
- APPROVED / REJECTED / NEEDS REVISION
```

---

### 5. Constraints

- ❌ MUST NOT modify code directly
- ❌ MUST NOT introduce new features
- ✅ Only analyze, critique, and suggest

## 4. Module Responsibility Division

- `core.protocol`: Defines AACP communication protocol Standard Format and Agent URI specifications.
- `core.dispatcher`: Implements the message dispatch center based on `asyncio.Queue`, supporting local routing and remote Egress (Tailscale/Nostr, etc.).
- `core.workspace`: Manages secure file storage areas (Blackboard) with Session isolation.
- `core.llm`: LLM engine abstraction layer, supporting Structured Outputs.
- `agents/`: Stores implementation logic for various types of Agents.
- `memory/`: (To be developed) Handles Token routing interception and long/short-term memory.

## 5. Key Interface Conventions

- **Agent URI**: Format is `{id}@{instance}` (e.g., `assistant_123@local`). `BROADCAST` is a special reserved address.
- **AACP Message**: Contains `message_id`, `timestamp`, `sender`, `receiver`, `intent`, `payload`, `context_pointer`.
- **Agent Callback**: Suggested signature is `async def handle_message(self, message: AACPMessage) -> None`.
- **System Intents**:
  - `SPAWN`: Dynamically create new Agent instances.
  - `TERMINATE`: Destroy specified Agent instances.
- **Structured Thinking**: Agents use the `AACPResponse` model for internal reasoning, then convert to `AACPMessage` for dispatch.

---
*This document will be continuously updated as the project progresses.*

