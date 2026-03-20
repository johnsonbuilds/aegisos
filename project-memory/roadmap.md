# AegisOS Roadmap

**Responsibility**
- Defines the long-term vision, phases, and core capabilities of the system.
- Answers what must be true at each stage and why, not how to implement it.

## Phase 1: The Core Kernel (Largely Completed)
**Goal**: Build the "motherboard" of AegisOS, implementing multi-agent dynamic collaboration under a standard protocol.

- [x] **AACP Protocol Definition**: Defined `AACPMessage` based on Pydantic v2, mandating the use of `context_pointer` to avoid passing large text blocks.
- [x] **WorkspaceManager (Blackboard System)**: Implicated a shared workspace based on the local file system, with strict path traversal defense.
- [x] **AegisDispatcher (Core Scheduler)**: An asynchronous event loop based on `asyncio`, supporting message routing, broadcasting, and lifecycle management.
- [x] **Kernel System Agent**: Implemented the `system@local` kernel agent, supporting SPAWN/TERMINATE dynamic management.
- [x] **E2E Collaboration Verification**: Dummy Agents ran through full-link tests including "Task Dispatch -> Dynamic Creation -> File I/O -> Destruction".

## Bridge Milestone: Single-Node MVP Baseline (Completed Ahead of Phase 2)
**Goal**: Prove the architecture can complete a real task loop before entering runtime hardening.

- [x] **Coordinator -> Worker -> Workspace -> Completion Loop**:
    - SPAWN a worker agent from a coordinator.
    - Execute a real task (web fetch / reporting).
    - Return result through AACP.
    - Support Worker termination flow.
- [x] **Real Tool Integration**:
    - Integrated HTTP fetch / scraping capability.
    - Avoided mock-only task execution.
- [x] **Workspace-based Task Flow**:
    - Wrote tasks and results into workspace files.
    - Passed `context_pointer` instead of large payloads.
    - Generated output artifacts such as reports.
- [x] **Runnable End-to-End Example**:
    - Example: `examples/fetch_and_report.py`.

## Phase 2: System Validation & Runtime Guardrails (Current Phase)
**Goal**: Turn the single-node MVP into a stable runtime by adding observability, bounded execution, termination correctness, and real-task validation gates.

- [ ] **Observability First**:
    - Log full AACP message flow with runtime trace metadata.
    - Trace task lifecycle and support session-level inspection.
    - Audit workspace writes with agent/task provenance.
- [ ] **Runtime Guardrails**:
    - Add `max_steps` loop protection for all agents.
    - Add bounded retry with exponential backoff.
    - Guarantee `TASK_COMPLETE -> TERMINATE` cleanup.
    - Enforce strong `plan.json` state transitions and atomic updates.
- [ ] **Minimal Safety**:
    - Add task/tool timeout and kill switch.
    - Tighten the current subprocess sandbox without overclaiming Zero-Trust completeness.
- [ ] **Real Task Validation**:
    - First stable loop: API monitor with deterministic execution path.
    - Daily web report loop.
    - Daily content generation loop.
- [ ] **Validation Gates**:
    - Runtime Ready gate.
    - First 24h stable real-loop gate.
    - 72h continuous validation gate.

## Phase 3: The Brain & Memory
**Goal**: Improve cognition efficiency only after the runtime becomes observable and stable.

- [ ] **LLM Engine Refinement**:
    - Continue Structured Outputs hardening across providers.
    - Improve prompt stability for `AACPResponse` generation.
- [ ] **MemoryManager (Memory Engine)**:
    - [ ] **Hot Memory**: Token-aware sliding window for recent dialogue and task status.
    - [ ] **Cold Memory**: Asynchronously extract facts into a lightweight vector store retrievable via RAG.
    - [ ] **Knowledge Distillation**: Background extraction of durable facts/preferences.
- [ ] **Dynamic Skill Routing**:
    - Introduce a lightweight classifier to mount only the most relevant skill prompts.
- [ ] **Prompt Caching**:
    - Reduce latency and cost for repeated resident instructions.
- [ ] **Early Multi-Node Communication (Exploratory)**:
    - Enable basic AACP messaging across nodes.
    - Validate remote agent addressing and simple cross-node execution.

## Phase 4: The Shield & Ecosystem
**Goal**: Ensure code execution safety and "legally hijack" the massive community skill market of OpenClaw.

- [ ] **SandboxRunner (Security Sandbox)**: Initially using restricted subprocesses, later upgrading to Docker or Firecracker containers.
- [ ] **HITL Fine-grained Permission Interceptor**: Sensitive actions (sending emails, committing code, connecting to the external network) trigger [Approve/Deny] authorization cards.
- [ ] **OpenClaw Compatibility Layer**: Automatically parse OpenClaw's `skill.md` and `action.py`, enabling plug-and-play ecosystem compatibility from day one.

## Phase 5: The Professional Team
**Goal**: Integrate open-source AI powerhouses for commercial-grade productivity.

- [ ] **OpenCode Programming Brain**: Encapsulated as `Coder_Agent`, performing closed-loop testing and maintaining project code in a cloud sandbox.
- [ ] **Firecrawl & Scrapling Data Armor**: Integrate visualized web-to-markdown conversion and heavy anti-crawler data collection.
- [ ] **CLI-Anything Action Translation Layer**: Wrap GUI software into headless JSON commands.
- [ ] **SOP Static Workflow Engine**: Support reading YAML-formatted SOP files, with standard collaboration processes allocated by a Planner.

## Phase 6: Economic Layer (Early Agent Economy)

**Goal**: Enable basic economic interactions between agents.

- [ ] **Task Pricing Model**:
    - Allow agents to attach price proposals to tasks
- [ ] **Simple Payment Integration**:
    - Integrate testnet-based payments (e.g., stablecoins)
- [ ] **Escrow Mechanism (Minimal)**:
    - Lock funds before task execution
    - Release funds upon TASK_COMPLETE
- [ ] **Agent Identity (Public Key)**:
    - Bind agent identity to cryptographic keys

## Phase 7: The Global Agent Network
**Goal**: Break through single-machine limitations to achieve distributed collaboration across devices and entities.

- [ ] **Evolutionary Egress Gateway Development**:
    - [ ] **Phase A**: URI resolution interception and Tailscale virtual LAN routing.
    - [ ] **Phase B**: Integrate Nostr Relays for public-key routing across firewalls.
    - [ ] **Phase C**: Fully enable Libp2p/WebRTC P2P hole punching.
- [ ] **AegisOS-Net (Go Sidecar)**: Independently develop a lightweight network daemon based on `go-libp2p` for DHT addressing.
- [ ] **IPC Communication Optimization**: Establish a high-performance cross-language communication bridge based on Unix Domain Sockets / gRPC.
- [ ] **CI/CD One-click Packaging System**: Cross-compile the Go engine and bundle it as a static resource within the Python Wheel package.
