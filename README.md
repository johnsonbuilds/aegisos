# AegisOS

An experimental operating system for autonomous AI agents.

AegisOS explores a new paradigm where AI agents are not just prompt chains or chatbot wrappers, but **long-running processes** that collaborate, communicate, and manage resources inside a structured runtime.

---

# Vision

Most current “AI agent frameworks” are essentially **chatbot wrappers** built around prompts.

They lack fundamental system primitives such as:

- process isolation
- structured communication
- resource scheduling
- persistent execution
- shared memory

As agents become more autonomous and long-running, these limitations become critical.

AegisOS explores what an **operating system for AI agents** could look like.

In this model, agents behave more like **processes** than chat sessions. They can:

- run continuously
- collaborate with other agents
- exchange structured context
- access shared artifacts
- spawn new agents
- operate inside a secure runtime

---

# Core Architecture

AegisOS follows a **microkernel-inspired architecture**.

The system separates coordination, communication, and execution into independent components.

```
Agents
   │
   │  AACP Protocol
   ▼
Dispatcher (task orchestration)
   │
   ▼
Workspace (shared artifacts & context)
   │
   ▼
Secure Execution Layer (WASM / Firecracker)
```

---

# Key Components

## Dispatcher

The **Dispatcher** acts as the system scheduler.

It manages:

- agent lifecycle
- task routing
- message delivery
- system orchestration

Agents do not call each other directly.
All collaboration happens through **protocol messages**.

---

## Workspace (Blackboard)

Agents collaborate through a controlled **shared workspace**.

Instead of sending large prompt payloads, agents exchange **references to artifacts** stored in the workspace.

Examples:

- documents
- intermediate outputs
- structured datasets
- task states

This dramatically reduces token usage and enables more scalable collaboration.

---

## AACP — Agent-to-Agent Context Protocol

AegisOS introduces **AACP**, a protocol designed for lightweight context exchange between agents.

Traditional agent systems pass large prompt histories between components.

AACP takes a different approach.

Agents exchange **structured messages containing context pointers** instead of raw data.

Example:

```json
{
  "intent": "summarize_document",
  "context_pointer": "/workspace/docs/report.md",
  "metadata": {
    "language": "en",
    "style": "technical"
  }
}
```

This allows agents to synchronize context state without transferring massive prompts.

---


# Agent Types

AegisOS supports multiple agent classes:

### LLM Agents

Reasoning-heavy agents powered by LLMs.

Responsibilities:

- planning
- reasoning
- task decomposition
- decision making

---

### Functional Agents

Deterministic agents optimized for execution.

Examples:

- file watchers
- scrapers
- code runners
- CLI automation

This hybrid model allows **LLMs to reason while deterministic agents execute**.

---

# Security Model

AegisOS follows a **zero-trust design**.

Agent skills run inside isolated environments such as:

- WebAssembly sandboxes
- Firecracker microVMs
- serverless runtimes

This protects the system from:

- prompt injection
- unauthorized filesystem access
- agent privilege escalation

High-risk actions require **Human-in-the-Loop approval**.

---

# Evolutionary Agent Network

AegisOS is designed to evolve from a local runtime to a distributed agent network.

Roadmap:

Stage 1

Local async message queue

Stage 2

Federated relay network

Stage 3

Fully decentralized P2P agent network

This architecture allows agents to collaborate across machines while maintaining the same protocol interface.

---

# Project Status

⚠️ Early research and development.

This repository currently contains:

- architecture design
- experimental prototypes
- protocol definitions
- development logs

The runtime is under active development.

---

# Devlogs

The design journey of AegisOS is documented in the `devlogs` directory.

Topics include:

- agent memory models
- multi-agent collaboration
- token-efficient architectures
- AACP protocol evolution

---

# Running Agents Today

AegisOS runtime is still under development.

If you want to run AI agents today, you can use our cloud platform:

https://getclawcloud.com/?utm_source=github

Currently supported:

- OpenClaw agents

AegisOS support will be added in future releases.

---

# License

MIT