# AegisOS Evolutionary Architecture

## Phase 1 (Current: MVP Rapid Acceleration)

- **Core Language**: Python 3.11+
- **Package Manager**: Strongly recommend using **uv** or **Poetry** (avoid native pip and requirements.txt to prevent dependency conflicts).
- **Multi-Agent Dispatching**: Abandon traditional multi-threading and fully embrace native **asyncio**. The AegisOS bus must be asynchronous (async/await) to efficiently handle I/O-intensive tasks such as agents waiting for LLM responses and file I/O.
- **Data Validation**: Use **Pydantic v2** as the cornerstone of the entire system, defining all AACP protocols and Agent states.

## Phase 2 (Future: When AegisOS Becomes True Infrastructure)

When the ecosystem explodes and requires simultaneous dispatching of hundreds of Agents with extreme security sandboxing, a multi-language microservice architecture will be adopted:

- **Control Plane (Message Bus)**: Rewrite the core scheduler `AegisDispatcher` using **Go** or **Rust**. Make it a highly stable system daemon with extremely low memory footprint (approx. 20MB).
- **Agent Plane (Agent Logic Layer)**: All Agent skills and the "brain" (LLM interaction layer) will remain in **Python**, communicating with the bus via local Sockets or gRPC.
