# Roadmap

Status: In Progress

### Phase 1: Core Kernel and Local Communication Bus [Substantially Complete]

**Goal**: Build the "motherboard" of AegisOS purely with code without mounting a real LLM. Prove that multiple agents can collaborate dynamically in a single-machine environment via standard protocols and shared files.

- [x] **Task 1.1: Standardized Communication Protocol (AACP)**
    - Define `AACPMessage` using Pydantic v2, ensuring all messages contain `context_pointer` to physically prevent large text blocks from passing through the bus.
- [x] **Task 1.2: Shared Workspace (Blackboard / WorkspaceManager)**
    - Establish sandbox directories based on the local file system (e.g., `_workspace/{session_id}`), implement asynchronous R/W, and add strict path traversal security checks.
- [x] **Task 1.3: Core Dispatcher (AegisDispatcher) and Kernel Agent**
    - Develop a global message event loop based on `asyncio`.
    - Build in `system@local` kernel agent for lifecycle management of `SPAWN` (dynamic sub-agent creation) and `TERMINATE` (agent destruction).
- [x] **Task 1.4: E2E Collaboration Validation**
    - Use Dummy Agents (hardcoded functions) to complete the full-link validation: "PM assigns task -> Create temp coder -> R/W workspace files -> Destroy coder."

### Phase 2: Cognitive Engine and Memory Synapses (The Brain & Memory) [In Progress]

**Goal**: Mount real LLMs (OpenAI/Claude) and thoroughly resolve the fatal pain point of traditional Agents (like OpenClaw) consuming 100k+ Tokens per request.

- [ ] **Task 2.1: LLM Engine and Structured Output Mounting**
    - Connect to LLM APIs, leveraging Structured Outputs to ensure all replies are strictly compliant AACP JSON, eliminating "hallucinated instructions."
- [ ] **Task 2.2: Dynamic Skill Routing**
    - Introduce small models (e.g., Llama-3-8B) as classifiers to intercept intents before main model execution, **mounting only the prompts of the 2-3 most relevant skills**, reducing context usage by 90%.
- [ ] **Task 2.3: Separation of Hot and Cold Memory (Memory Manager)**
    - **Hot Memory**: Implement a sliding window to retain only the last 5 dialogue rounds and the current task state summary.
    - **Cold Memory**: Run small background agents to summarize old dialogues into "Facts" for storage in a lightweight vector database (e.g., Chroma), awakened anytime via RAG.
- [ ] **Task 2.4: Prompt Caching**
    - Enable system-level caching at the API layer for resident system instructions and core skills to drastically reduce cost and latency.

### Phase 3: Zero-Trust Sandbox and Legacy Ecosystem Compatibility (The Shield & Ecosystem)

**Goal**: Allow Agents to safely execute real code and actions while "legally stealing" the vast community skill market of OpenClaw.

- [ ] **Task 3.1: Serverless/Containerized Sandbox Executor (SandboxRunner)**
    - Develop a secure execution environment (initially using strictly limited Python `subprocess`, later upgrading to Docker containers or Firecracker VMs) to isolate the host system.
- [ ] **Task 3.2: HITL Fine-Grained Permission Interceptor (Human-in-the-loop)**
    - Embed interceptors in the gateway layer. When an Agent attempts sensitive actions (emailing, committing code, network requests), pause the system and send structured [Approve/Deny] authorization cards via console or IM tools.
- [ ] **Task 3.3: OpenClaw Compatibility Layer**
    - Write a converter to automatically parse OpenClaw-formatted `skill.md` and `action.py`, encapsulating them as native AegisOS skills for downgraded execution in the secure sandbox.

### Phase 4: Professional Heavy Weapons and Business Flow Orchestration (The Professional Team)

**Goal**: Natively integrate the four open-source AI powerhouses specified in the PRD into AegisOS for commercial-grade productivity, and introduce process-based management.

- [ ] **Task 4.1: Integrate OpenCode (Dedicated Programming Brain)**
    - Encapsulate OpenCode as a standard `Coder_Agent` for code writing, self-evolution, and project maintenance, with closed-loop testing in a cloud sandbox.
- [ ] **Task 4.2: Integrate Firecrawl & Scrapling (Vision and Heavy Data Armor)**
    - Encapsulate Firecrawl as a `Vision_Agent` to convert web pages to clean Markdown, avoiding energy consumption and prompt injection risks of headless browsers.
    - Encapsulate Scrapling as a `Scraper_Agent` for heavy data tasks requiring Cloudflare bypass and 24/7 monitoring.
- [ ] **Task 4.3: Integrate CLI-Anything (Precision Action Translation Layer)**
    - Encapsulate GUI software as headless JSON commands, abandoning fragile mouse click simulations.
- [ ] **Task 4.4: SOP Static Workflow Engine**
    - Support reading YAML-formatted SOP files, allowing the main Agent (Planner) to assign and dispatch multi-agent collaboration based on fixed corporate standards.

### Phase 5: Ultimate Gateway and P2P Star Network (The Distributed Future)

**Goal**: Break through single-machine limits to enable communication between multiple devices (mobile, PC, cloud) and different entities (cross-enterprise collaboration), completing the "OS" puzzle.

- [ ] **Task 5.1: Evolutionary Gateway Development (Egress Gateway)**
    - **Evolution Path**:
        1. **V1**: Support Tailscale virtual LAN routing using existing encrypted links.
        2. **V2**: Integrate Nostr Relay for cross-firewall addressing via public keys.
        3. **V3**: Fully enable `go-libp2p` / WebRTC P2P hole punching and DHT routing.
- [ ] **Task 5.2: Go Network Sidecar Development (AegisOS-Net Daemon)**
    - Develop a ultra-lightweight (~20MB) P2P network daemon using Go and the `go-libp2p` library.
- [ ] **Task 5.3: IPC Cross-Language Communication Bridge**
    - Establish a communication mechanism between the Python main process and Go daemon based on local Unix Domain Sockets (UDS) or localhost gRPC.
- [ ] **Task 5.4: CI/CD One-Click Packaging System**
    - Configure automated pipelines to cross-compile Go source code into executables for three major operating systems and bundle them as static resources into the Python `.whl` package.
