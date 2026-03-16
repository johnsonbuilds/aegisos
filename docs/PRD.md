# Product Definition

# 1. Product Overview and Positioning

- **Product Name**: AegisOS (provisional name)
- **Product Positioning**: A next-generation, secure, efficient AI Agent Operating System with native support for multi-agent collaboration.
- **Core Vision**: To complete the paradigm shift from "Chatbot Wrappers" to an "Agentic OS." AegisOS aims to provide a 24/7, multi-channel autonomous execution experience while thoroughly resolving the severe security risks and excessive resource consumption found in previous generation products (e.g., OpenClaw).

# 2. Core Pain Points and Resolution Strategies

AegisOS is specifically designed to refactor the three fatal flaws of existing mainstream Agent products:

| **Existing Pain Points (e.g., OpenClaw)** | **AegisOS Resolution Strategy** |
| --- | --- |
| **High-Risk Security Vulnerabilities**: Over-reliance on local Root permissions, susceptible to prompt injection attacks leading to malicious operations or account bans. | **Zero-Trust and Serverless Sandboxing**: Abandon local host execution; skills run in disposable sandboxes like cloud-based WebAssembly or Firecracker VMs. |
| **High Maintenance Barrier**: Excessive memory footprint; difficult for non-developers to configure for stable 24/7 background operation. | **Lightweight Architecture**: Decouple high-energy-consumption GUI automation and headless browsers in favor of pure API/CLI protocol interactions. |
| **Uncontrolled Autonomous Execution**: AI performing unauthorized high-risk operations (e.g., transfers, large-scale scraping). | **HITL Fine-Grained Permission Control**: Low-level interceptors require humans to authorize sensitive operations via structured cards (Approve/Deny) sent through IM tools. |

# 3. Core Functions and Engine Architecture

The underlying engine of AegisOS will deeply integrate cutting-edge open-source projects to build powerful professional modules:

- **Action Translation Layer (Integrated with CLI-Anything)**: Abandon fragile visual model click simulations. Encapsulate open-source GUI software as CLI tools with deterministic JSON output. LLMs call software accurately and headlessly by outputting secure JSON commands.
- **Dedicated Programming Brain (Integrated with OpenCode)**: An independent programming Agent in a cloud sandbox, responsible for generating, validating, and testing new skill code to ensure the quality and safety of self-evolving Agent code.
- **Secure Vision and Reading Senses (Integrated with Firecrawl)**: Replace energy-intensive built-in browsers. Obtain clean, LLM-friendly Markdown or structured data from URLs without malicious scripts, significantly reducing prompt injection risks.
- **Heavy Data Collection Armor (Optional Integration with Scrapling)**: Deploy a highly adaptive scraping framework to automatically bypass anti-scraping mechanisms and adapt to UI updates, ensuring uninterrupted 24/7 background scraping.

# 4. Key Technical Solutions (Addressing OS Essence and Cost Bottlenecks)

### 4.1 Ecosystem Inheritance and Sandbox Downgraded Execution

- **OpenClaw Compatibility Layer**: Built-in converter to automatically parse OpenClaw's vast third-party `skill.md` ecosystem.
- **Safety Downgrade**: Mandatory injection of external code into cloud Serverless sandboxes or Docker containers for execution, isolating risks and achieving day-one plug-and-play compatibility.

### 4.2 Minimal Token Consumption and Memory Breakthrough

To break through input Token limits and achieve unlimited contextual dialogue, AegisOS will utilize a three-tier storage engine and routing mechanism:

- **Dynamic Skill Routing**: Use small models (e.g., Llama-3-8B) for intent classification. Each request mounts only the 2-3 most relevant skill descriptions in the main model's prompt, reducing context usage by 90%.
- **Separation of Hot and Cold Memory**:
    - **Hot Memory (RAM)**: Retains only the 5 most recent dialogue rounds and the current task's "State Summary."
    - **Cold Memory (Disk)**: Dialogues beyond 5 rounds are asynchronously summarized into "Facts" and "Preferences" by a small model and stored in a Vector DB. RAG (Retrieval-Augmented Generation) retrieves specific fragments only when historical events are mentioned.
- **Global Prompt Caching**: Fully enable Prompt Caching for the underlying model API to cache static system settings and high-frequency skills.

### 4.3 Native Multi-Agent Collaboration Bus

Agents communicate through standardized digital "corporate organizations" instead of long-winded natural language:

### A. Standardized Communication Protocol (AACP) Design

We replace open-ended natural language "chatting" between Agents (which causes Token explosions) with a minimalist JSON protocol. Each message includes:

- **header**: Contains `sender`, `receiver` (an Agent or public channel), and `intent` (e.g., Request, Propose, Inform, Reject, Task_Complete).
- **payload**: Structured task descriptions or execution results.
- **context_pointer**: **Crucial!** Agents pass pointers (URLs or file paths) rather than lengthy documents.

### B. Introduction of "Blackboard System" and "Shared Workspace"

Human teams collaborate by **sharing Git repositories or cloud documents** rather than sending hundreds of megabytes of code and docs back and forth. AegisOS creates a "Shared Workspace" for each project.

- For example, a "Research Agent" writes findings to `research.md` in the workspace.
- Upon completion, it sends a standard protocol message to the "Writing Agent": `{"intent": "Task_Complete", "pointer": "/workspace/research.md"}`.
- The Writing Agent then reads the file directly from the workspace.

### C. "SOP (Standard Operating Procedure)" as the Collaboration Backbone

Human organizations run on processes. AegisOS supports YAML-defined SOP workflows. You can preset:

- Step 1: Requirements Analysis Agent intervenes.
- Step 2: If requirements are clear, dispatch to Code Agent (OpenCode); if external data is needed, dispatch to Data Agent (Firecrawl).
- Step 3: Test Agent reviews; if it fails, returns to Code Agent.
