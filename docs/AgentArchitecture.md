From the perspectives of engineering implementation and system evolution (Evolutionary Architecture), introducing "different types of Agents" typically has the following three core values and meanings:

### A. Cognitive Cost and Resource Efficiency
- **AACPAgent (Heavy)**: Every round of dialogue and every action requires calling an LLM. This involves expensive Token costs and high Latency.
- **Stub/Functional Agent (Light)**: Some tasks are deterministic and repetitive, such as a `FileWatcherAgent` (monitoring file changes) or a `LinterAgent` (specifically running code checks). Asking an LLM to "think" about how to run `ls` is an extreme waste of resources.
- **Conclusion**: In AegisOS, we need both "kernel-space" fast agents (System Daemons) and "user-space" intelligent agents (LLM Agents).

### B. Determinism and Safety
- LLMs are probabilistic. Even with a well-written prompt, they may hallucinate at critical stages (e.g., deleting a database, sending an email).
- Functional Agents ensure 100% determinism on critical system paths through hardcoded logic.

### C. Cross-Language and Heterogeneous Integration
- Our RoadMap (Phase 5) mentions a Go-Sidecar.
- If an Agent is a high-performance network gateway written in Go, it appears as a `ProxyAgent` class on the Python side. It doesn't need an LLM engine; it only needs to pass AACP messages through to the Go process.
