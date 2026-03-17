# AegisOS Roadmap

## Phase 1: The Core Kernel (Largely Completed)
**Goal**: Build the "motherboard" of AegisOS, implementing multi-agent dynamic collaboration under a standard protocol.

- [x] **AACP Protocol Definition**: Defined `AACPMessage` based on Pydantic v2, mandating the use of `context_pointer` to avoid passing large text blocks.
- [x] **WorkspaceManager (Blackboard System)**: Implicated a shared workspace based on the local file system, with strict path traversal defense.
- [x] **AegisDispatcher (Core Scheduler)**: An asynchronous event loop based on `asyncio`, supporting message routing, broadcasting, and lifecycle management.
- [x] **Kernel System Agent**: Implemented the `system@local` kernel agent, supporting SPAWN/TERMINATE dynamic management.
- [x] **E2E Collaboration Verification**: Dummy Agents ran through full-link tests including "Task Dispatch -> Dynamic Creation -> File I/O -> Destruction".

## Phase 2: The Brain & Memory (Current Phase)
**Goal**: Integrate real Large Language Models (LLMs) and address pain points in Token consumption and context management.

- [ ] **LLM Engine Integration**: Interface with OpenAI/Claude APIs, mandating Structured Outputs to eliminate hallucinated instructions.
- [ ] **MemoryManager (Memory Engine)**:
    - [ ] **Hot Memory**: Implement a sliding window mechanism to retain the last 5 rounds of dialogue and current task status.
    - [ ] **Cold Memory**: Asynchronously extract "Facts" into a lightweight vector store (Chroma), retrievable via RAG.
- [ ] **Dynamic Skill Routing**: Introduce a small classifier to intercept intents and mount only the 2-3 most relevant skill prompts.
- [ ] **Prompt Caching**: Enable system-level caching at the API level to reduce latency and costs for resident instructions.
- [ ] **Basic Multi-Node Communication (Early Network Layer)**:
    - Enable AACP messaging across multiple nodes (non-P2P, simple relay or direct connection is acceptable)
    - Support remote agent addressing (agent@node)
    - Validate cross-node task execution

## Phase 3: The First Working Loop (Single-Node MVP)

**Goal**: Validate that AegisOS can complete a real-world task autonomously within a single node.

- [ ] **Single Agent Task Loop**:
    - SPAWN a worker agent from a coordinator
    - Execute a real task (not dummy)
    - Return result via AACP
    - TERMINATE agent

- [ ] **Real Tool Integration**:
    - Integrate at least one real external capability (e.g., HTTP fetch / scraping)
    - Avoid mock tools

- [ ] **Workspace-based Task Flow**:
    - Write task into workspace
    - Pass context_pointer
    - Generate output artifact (e.g., report.md)

- [ ] **End-to-End Example**:
    - Example: "Fetch a webpage and generate a summary report"
    - Must be runnable as a demo script

- [ ] **Observability**:
    - Log full AACP message flow
    - Trace task lifecycle

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
