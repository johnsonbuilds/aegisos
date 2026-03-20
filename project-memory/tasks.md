# AegisOS Active Tasks (Phase 2 Focus)

## Recent Review (Phase 1 Archive)
- [x] **Core Kernel Implementation**: Dispatcher, Workspace, Protocol, and Kernel Agent are online.
- [x] **Security and Stability**: Completed edge case unit tests and released the AACP protocol specification document.

## Current Focus (Phase 2: Cognitive Engine & Memory)
### Task 5: LLM Engine & AACPAgent Integration
- [x] **LLM Engine Implementation**: Completed OpenAI/Anthropic asynchronous adapters.
- [x] **AACPAgent Base Class**: Implemented structured decision loops.
- [x] **Async Callback Integration**: Successfully registered `AACPAgent.handle_message` as a callback function in `AegisDispatcher`, supporting dynamic spawning (SPAWN) via `system@local`.
- [ ] **Prompt Optimization**: Optimize AACP response stability for different models to reduce formatting hallucinations.
- [ ] **Prompt Caching**: Utilize API caching to reduce costs for repetitive instructions.

### Task 6: Memory Manager Implementation
- [ ] **Hot Memory (Sliding Window)**:
    - [ ] Implement `MemoryManager.add_message()`.
    - [ ] Implement automatic truncation logic based on Token counts or round numbers.
    - [ ] Integrate into `AACPAgent` to replace existing simple list history.
- [ ] **Cold Memory (Vector Database)**:
    - [ ] Integrate ChromaDB or Qdrant.
    - [ ] Implement an asynchronous RAG retrieval flow.
- [ ] **Knowledge Distillation**:
    - [ ] Implement background tasks to automatically extract "Facts/Preferences" from hot memory and store them in cold memory.

### Task 7: Basic Security Sandbox

- [x] **SandboxRunner**: Implemented Python code execution isolation based on restricted subprocesses.
- [ ] **HITL Interceptor**: Define approval workflows for sensitive actions.

- [x] **First Real Task Loop (Single-Node MVP)**:
    - [x] **Coordinator/Worker Implementation**: Refactored to align with Cognitive Architecture Mapping (Externalized State).
    - [x] **WebScraping Skill**: Implemented a pluggable `WebScraperSkill` using `httpx`.
    - [x] **Pluggable WebFetch Architecture**: Refactored `WebFetchSkill` with `BaseFetchEngine` abstraction, supporting multiple engines (MVP: `SimpleHttpEngine`).
    - [x] **Workspace-based Task Flow**: Validated that agents can read/write via `context_pointer` and structured indexing.
    - [x] **End-to-End Logic Verification**: Verified full lifecycle via mock tests in `tests/test_cognitive_architecture.py`.
    - [x] **Runnable Demo**: Provided `examples/fetch_and_report.py`.

---
*Note: For long-term planning, please see [Roadmap](./roadmap.md)*
