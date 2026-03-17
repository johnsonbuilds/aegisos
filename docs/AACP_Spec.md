# AACP — Agent-to-Agent Communication Protocol
## Draft Specification v1
---

# 1. Overview
AACP (Agent-to-Agent Communication Protocol) defines a standardized protocol for communication between autonomous agents operating within the AegisOS ecosystem or compatible runtimes.

The protocol enables agents to:

+ send structured messages
+ request services
+ coordinate tasks
+ exchange results
+ manage agent lifecycle
+ collaborate across distributed networks

AACP is designed to support **heterogeneous agent implementations**, meaning that any system capable of sending and receiving valid AACP messages can participate in the network.

---

# 2. Design Goals
The protocol is designed around five core principles.

### 2.1 Deterministic Communication
Messages must be machine-readable and deterministic.

AACP uses structured formats rather than natural language messaging to ensure reliability.

---

### 2.2 Protocol-Level Interoperability
Agents implemented in different languages or frameworks must be able to communicate as long as they implement the AACP specification.

---

### 2.3 Separation of Semantics
The protocol distinguishes between:

Intent (communication semantics)

and

Action (application-level behavior)

This separation allows the protocol to remain stable while application capabilities evolve.

---

### 2.4 Large Context Efficiency
Agents should avoid transferring large data through messages.

Instead, AACP supports **context pointers** referencing shared workspace artifacts.

---

### 2.5 Network Compatibility
AACP must function across:

+ local processes
+ distributed nodes
+ peer-to-peer networks

---

# 3. Agent Identity
Each agent participating in the network must have a globally unique identity.

### Agent URI Format
```plain
{role}_{uuid}@{node_id}
```

Example:

```plain
planner_9f3c@node42
coder_17ab@laptop.local
researcher_a81f@12D3KooWabc...
```

Components:

| Field | Description |
| --- | --- |
| role | functional role of the agent |
| uuid | unique instance identifier |
| node_id | host node or public key |


---

# 4. Message Structure
Every AACP message follows a standardized schema.

Example:

```json
{
  "message_id": "uuid",
  "timestamp": "ISO8601",
  "sender": "agent_uri",
  "receiver": "agent_uri",
  "intent": "REQUEST",
  "payload": {},
  "context_pointer": "/workspace/task_123.json"
}
```

### Field Definitions
| Field | Description |
| --- | --- |
| message_id | unique message identifier |
| timestamp | creation time |
| sender | agent sending the message |
| receiver | target agent |
| intent | communication primitive |
| payload | application data |
| context_pointer | reference to workspace artifact |


---

# 5. Intent Layer
Intent defines the **communication semantics** of a message.

Supported intents in v1:

| Intent | Purpose |
| --- | --- |
| REQUEST | ask another agent to perform an action |
| PROPOSE | respond with an offer or proposal |
| INFORM | send informational updates |
| ERROR | report failure or exception |
| TASK_COMPLETE | report task completion |
| SPAWN | request creation of a new agent |
| TERMINATE | request destruction of an agent |


---

# 6. Action Layer
The action layer defines the **specific operation requested**.

Actions are encoded in:

```plain
payload["action"]
```

Example:

```json
{
  "intent": "REQUEST",
  "payload": {
    "action": "core.exec.code",
    "language": "python",
    "code": "print('hello')"
  }
}
```

Actions follow a namespace format:

```plain
<domain>.<category>.<operation>
```

Examples:

| Action | Description |
| --- | --- |
| core.exec.code | execute code |
| core.fs.read | read file |
| core.fs.write | write file |
| web.search | web search |
| skill.scrape | web scraping |


---

# 7. Context Pointer
Large data should not be embedded directly in messages.

Instead, agents use a **context pointer** referencing workspace storage.

Example:

```plain
_workspace/session123/report.md
```

Benefits:

+ reduces token usage
+ enables multi-agent collaboration
+ allows persistent artifacts

---

# 8. Agent Lifecycle
Agents may be dynamically created and destroyed.

Lifecycle control is handled through the system agent.

Example:

```plain
sender: planner@node
receiver: system@node
intent: SPAWN
payload:
  agent_type: coder_agent
```

Lifecycle flow:

```plain
SPAWN → WORK → TASK_COMPLETE → TERMINATE
```

---

# 9. Error Handling
Errors must be reported through the ERROR intent.

Example:

```json
{
  "intent": "ERROR",
  "payload": {
    "error_type": "execution_error",
    "message": "python exception"
  }
}
```

Agents receiving errors may attempt recovery or retry strategies.

---

# 10. Security Considerations
Implementations must ensure:

+ authentication of sender identity
+ authorization for sensitive actions
+ sandboxing of executed code
+ validation of payload structures

Future versions may integrate:

+ signature verification
+ encrypted payloads
+ trust scoring

---

# 11. Network Transport
AACP is transport-agnostic.

Possible transports include:

+ local IPC
+ gRPC
+ WebSocket
+ libp2p streams
+ HTTP

This allows AACP to function across diverse environments.

---

# 12. Future Extensions
Future protocol versions may introduce:

+ capability negotiation
+ economic transaction primitives
+ agent reputation metadata
+ service discovery messages

---