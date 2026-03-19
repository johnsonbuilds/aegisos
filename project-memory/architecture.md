# AegisOS Architecture

## 1. System Layers
- **Control Plane**: Responsible for the message bus (AegisDispatcher), Agent addressing, lifecycle management, and system security interception.
- **Agent Plane**: Runs specific Agent logic, LLM interaction layers, and Skills that perform specific tasks.
- **Data Plane (Workspace)**: Shared workspace (Blackboard System), managing large-scale data shared between Agents via the file system.
- **Network Plane (Distributed Agent Network)**
- **Economic Plane (Agent Economy & Settlement)**

## 2. Network Plane (Distributed Agent Network)

- Responsible for cross-node communication between agents
- Supports agent addressing via URI (`agent@node`)
- Enables peer discovery and routing (future: DHT/libp2p)
- Abstracted through the Evolutionary Egress Gateway

This layer transforms AegisOS from a local runtime into a distributed agent network.

## 3. Economic Plane (Agent Economy)

- Enables agents to participate in economic activities
- Supports task pricing, negotiation, and settlement
- Integrates with blockchain-based payment systems
- Provides the foundation for autonomous service exchange

This layer is essential for evolving AegisOS into a self-organizing agent economy.

## 4. Core Components
### 4.1 AegisDispatcher (Core Scheduler)
- Asynchronous message routing based on `asyncio.Queue`.
- Maintains a global registry, supporting the `system@local` kernel proxy.
- Handles routing and broadcasting of AACP messages.

### 4.2 Evolutionary Egress Gateway
- **Abstraction Layer**: Abstracts `Network Gateway` within `AegisDispatcher`, shielding upper-layer Agents from underlying network addressing details.
- **Evolutionary Stages**:
  - **Stage 1 (Private Cloud)**: Virtual LAN routing based on Tailscale/WireGuard, utilizing fixed virtual IPs for communication.
  - **Stage 2 (Federated Relay)**: Federated Relay based on WebSocket + Pub/Sub (similar to the Nostr protocol), where messages are encrypted with public keys and forwarded by relays to solve cross-firewall penetration.
  - **Stage 3 (Pure P2P)**: Fully decentralized network based on Libp2p/DHT, achieving Web3-level point-to-point connectivity.

### 4.3 WorkspaceManager (Blackboard Pattern Manager)
- Responsible for the directory lifecycle of `_workspace/{session_id}`.
- Provides `write_file` / `read_file` asynchronous interfaces.
- **Security**: Built-in path traversal validation to ensure all I/O is confined within the workspace.

### 4.4 AACP (Agent-to-Agent Communication Protocol)
- **Format**: JSON (Pydantic model).
- **Fields**: `message_id`, `timestamp`, `sender`, `receiver`, `intent`, `payload`, `context_pointer`.
- **Layer Mapping**:
    - **context_pointer = cognitive state (Cognitive Layer)**: Index + Directive.
    - **payload = execution data (Execution Layer)**: Transient input for actions.
    - **intent = control signal (Dispatch Layer)**: Communication primitives.
- **Communication Primitives (Intent)**: REQUEST, PROPOSE, INFORM, TASK_COMPLETE, ERROR, SPAWN, TERMINATE.
- **Business Actions (Action)**: Business logic is defined via `payload["action"]` and normalized by the `AACPAction` enum (e.g., `core.exec.*`, `core.fs.*`), achieving complete decoupling between the protocol and business layers.

### 4.5 OpenClaw Compatibility Layer
- Responsible for automatically parsing the OpenClaw third-party `skill.md` market ecosystem.
- **Security Downgrade**: Loaded external code is forced into cloud Serverless sandboxes or Docker containers for execution, ensuring plug-and-play ecosystem compatibility from day one.

## 5. Addressing and Collaboration Mechanism
### 5.1 Agent URI
Uses an email-like addressing standard: `{role}_{uuid}@{instance_id}`.
- **Local Address**: `planner@local`.
- **Remote Address**: `planner@macbook-pro.local` (Tailscale) or `planner@{public_key}` (Nostr/P2P).

### 5.2 Shared Workspace Pointer (Context Pointer)
Agents do not pass large data blocks between them; instead, they pass state references and execution pointers via the `context_pointer`.

- **Structure**:
    - `current_task`: Execution pointer (e.g., "task_3"). Allows zero-thinking execution by the receiver.
    - `uri`: State reference (e.g., "_workspace/plan.json"). Provides deep information on-demand.

#### 5.2.1 Payload Responsibility Boundary (Precise Definition)
The `payload` serves strictly as "action input" and "transient state," and must adhere to the following constraints:

**✅ Whitelist (Allowed):**
1. **Action (Core)**: Target capability and its arguments (e.g., `core.fs.write`).
2. **Tool / Execution Parameters**: Runtime parameters passed to specific tools.
3. **Transient Return Values**: Non-persistent, non-critical, and non-reusable states (e.g., `status: started`).

**❌ Blacklist (Strictly Forbidden):**
1. **Task Definition**: Must not contain specific steps or task descriptions.
2. **Plan / Graph**: Execution plans must be stored in the Workspace.
3. **Memory / History**: Dialogue history or cognitive records.
4. **Long-term Value Reasoning (Analysis)**: Any valuable analytical results must be stored in workspace files.

#### 5.2.2 Context Pointer Responsibility Boundary
The `context_pointer` represents the "State of the World" and must include two complementary types of information:

1. **Execution Pointer**: `current_task`. Ensures the Agent knows exactly what to execute without further reasoning.
2. **State Reference**: `uri`. Points to physical files in the Workspace, allowing the Agent to read deep information on-demand.

---

### 5.3 Dynamic Lifecycle (Kernel Control)
The main proxy dynamically creates and destroys temporary sub-agents by sending SPAWN/TERMINATE messages to `system@local`, achieving on-demand resource allocation.

### 5.4 SOP Workflow (Standard Operating Procedure)
- In addition to dynamic agent creation, the system supports reading YAML-formatted SOP files as a static backbone for multi-agent collaboration flows.
- Defines steps, distribution rules, and feedback mechanisms (e.g., Requirements -> Coding -> Testing -> Rejection/Retry).

### 5.5 Dynamic Skill Routing
- Uses minimal models (e.g., Llama-3-8B) for real-time intent classification.
- Each request mounts only the 2-3 most relevant skill descriptions in the main model's prompt, reducing context usage by 90%.
- Fully enables Prompt Caching for underlying model APIs.

### 5.6 Inter-process Communication (IPC via UDS/gRPC)
- **Sidecar Pattern**: The Python main process handles AI logic and scheduling, while a Go daemon (`aegisos-net`) handles the underlying Libp2p network and DHT addressing.
- **Low-latency Bridge**: Both communicate at high speed via local **Unix Domain Socket (UDS)** or **localhost gRPC**.
- **Workflow**: The Python side delivers remote messages to the local socket -> the Go process parses and routes them to the global network.

## 6. Key Capability Engines
AegisOS extends its capabilities by integrating specialized engines:
- **CLI-Anything (Action Translation Layer)**: Wraps open-source GUI software as CLI tools with deterministic JSON output.
- **OpenCode (Programming Brain)**: An independent programming agent in a cloud sandbox, responsible for generating, verifying, and testing new skill code.
- **Firecrawl (Security Vision & Reading)**: Replaces high-energy browsers, obtaining clean Markdown or structured data.
- **Scrapling (Data Collection Armor)**: A highly adaptive crawler framework that bypasses anti-crawl mechanisms and adapts to UI updates.

## 7. Cognitive Architecture Mapping
This is the core soul that distinguishes AegisOS from ordinary scripts, transforming core AI paradigms into physical component mappings.

### 7.1 Task Decomposition & Planning (Plan-and-Solve)
- **Theoretical Mapping**: Abandons maintaining a massive Todo List in the LLM memory window, forcing mapping to the **Shared Workspace (Blackboard)** and **SOP Engine**.
- **Implementation Specification**: The main agent must materialize decomposed sub-tasks into physical files (e.g., `_workspace/plan.json`) and dispatch tasks via the `context_pointer` in AACP messages. This makes the planning process persistent and supports multi-agent asynchronous collaboration.

### 7.2 ReAct Paradigm (Reasoning + Acting)
- **Theoretical Mapping**: Abandons the traditional while-loop single-threaded trap, mapping completely to the **AegisDispatcher (Core Scheduler)** and **AACP Communication Bus**.
- **Implementation Specification**: Agent "Thinking (Thought)" is done internally; "Action" is manifested as sending an AACP message with a specific Intent; "Observation" is manifested as receiving execution results from the target node (e.g., a CLI-Anything plugin) via the Dispatcher. This achieves system-level ReAct decoupling.

### 7.3 Reflexion & Self-Correction
- **Theoretical Mapping**: System-level crash interception, mapped to **SandboxRunner (Security Sandbox)** and **AACP ERROR intent**.
- **Implementation Specification**: When code generated by the dedicated programming agent (OpenCode) crashes in the sandbox, AegisOS is never allowed to go down. The sandbox must encapsulate the Error Traceback as an AACP ERROR message and send it back to the agent, triggering the agent's internal reflection prompts to automatically fix the code and retry.

### 7.4 State Tracking & Final Verification
- **Theoretical Mapping**: Mapped to the **Kernel System Agent (system@local)** and **Lifecycle Management**.
- **Implementation Specification**: When a sub-task is completed, a `TASK_COMPLETE` message must be sent. The main agent performs result acceptance (Critic) via the workspace; once accepted, the main agent must send a `TERMINATE` instruction to the system agent to gracefully destroy the temporary sub-agent and release system resources.

### 7.5 Coordinator-Worker Collaboration Pattern
AegisOS enforces a strict separation between decision-making and execution. This design choice is part of the **Phase-1 architecture**, prioritizing determinism, debuggability, and system stability.

- **Coordinator (Main Agent / Planner)**:
    - Responsible for reading/updating the global plan (`plan.json`).
    - Decides the next task to execute.
    - Writes the `current_task` into the `context_pointer` during dispatch.
- **Worker (Execution Agent)**:
    - Only responsible for executing the `current_task` assigned in the `context_pointer`.
    - Does not make decisions about task sequencing or overall planning.

**Future Evolution**: 
Subsequent iterations will introduce **Hierarchical Delegation**, enabling controlled decentralization of decision power without compromising global consistency.

**Standard Workflow**:
1. **Plan Generation**: Coordinator creates `_workspace/plan.json`.
2. **Task Selection**: Coordinator reads the plan and selects a pending task (e.g., `task_2`).
3. **Context Injection**: Coordinator writes `{"uri": "_workspace/plan.json", "current_task": "task_2"}` into the `context_pointer`.
4. **Dispatch**: Coordinator sends a message with `intent: TASK_EXECUTE` to the Worker.
5. **Execution & Feedback**: Worker executes the task, writes results to the workspace, and sends `TASK_COMPLETE` back to the Coordinator.
6. **Plan Update**: Coordinator updates `plan.json` and repeats the cycle.

### 7.6 Context Access Model (Lazy Cognitive Loading)

To preserve the separation between system-level cognition and prompt-based reasoning, AegisOS enforces a strict **lazy-loading model** for externalized state.

- **No Full Auto-Inspection**:
    
    Agents MUST NOT automatically preload full workspace files (e.g., `plan.json`) into the prompt.
    
- **Context Pointer as Index, Not Payload**:
    
    The `context_pointer` provides:
    
    - a **minimal execution directive** (e.g., `current_task`)
    - a **reference to external state** (`uri`)

- **On-Demand Access**:
    
    Agents must explicitly retrieve additional context via system skills (e.g., `FILE_READ`) when needed.
    
- **Lightweight Injection Only**:
    
    The system may inject:
    
    - task identifiers
    - high-level summaries
    
    But MUST NOT inject full state content.
    
**Rationale**:

- Prevents token explosion
- Avoids cognitive noise
- Ensures cognition remains externalized and composable
- Preserves system-level observability

## 8. Tech Stack

- **Core Language**: Python 3.11+
- **Package Management**: uv
- **Asynchronous Framework**: asyncio / aiofiles
- **Data Validation**: Pydantic v2

## 9. Storage & Memory Collaboration Model

AegisOS adopts a "Desk + Brain" dual storage model, clearly dividing the responsibilities between `WorkspaceManager` and `MemoryManager`:

### 9.1 WorkspaceManager (Desk / External Hard Drive)

- **Positioning**: Manages **persistent data assets (Artifacts)** and **multi-agent shared environments (Blackboard)**.
- **Responsibilities**:
    - **Big Data Handling**: Stores large files (requirement docs, source code, datasets) that LLMs cannot fit directly into context.
    - **Deliverables Management**: Records final outputs generated by Agents (code files, reports, images).
    - **Security Isolation**: Provides Session-based path traversal protection, ensuring Agents only operate within authorized workspaces.
- **Collaboration Mode**: Passing file paths via `context_pointer` in AACP messages.

### 9.2 MemoryManager (Brain / Cognitive Cache)

- **Positioning**: Manages **cognitive continuity**, **session context**, and **Token window safety**.
- **Responsibilities**:
    - **Hot Memory**: Maintains recent dialogue history and Chain of Thought, implementing automatic truncation and Token optimization.
    - **Cold Memory**: Asynchronously extracts key facts and preferences into a vector database for long-term knowledge accumulation.
    - **Cognitive Filtering**: Before sending to the LLM, reconstructs or compresses history based on task relevance (Summarization).
- **Collaboration Mode**: Mounted directly in the `AACPAgent` instance as its source of context for reasoning.
