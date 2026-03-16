# Agent-to-Agent Communication Protocol

We need to design forward-looking business scenarios for AegisOS. In traditional software, functions are statically hardcoded; however, in our vision for AegisOS, **Agents are not just "executors," but also "managers" and "creators."** This closely resembles the process management mechanism in Linux (where a main process `forks` child processes, `kills` them after tasks are finished, and communicates via IPC).

To perfectly support **"peer collaboration, dynamic parent-child hierarchies, temporary worker destruction, and cross-instance communication,"** we need to upgrade the underlying architecture of AegisOS across the following **4 dimensions**:

### 1. Unified Addressing System (Agent URI): Like Assigning "Corporate Emails"

To support complex communication (master-slave, peer, cross-instance), we cannot use simple names like "Coder" for Agents. We need to introduce the **Agent URI (Uniform Resource Identifier)** mechanism.

All Agent IDs must follow an email-like format:

`{role}_{uuid}@{instance_id}`

- **Independent Main Agent (Permanent)**: `planner@local`
- **Peer Agent (Permanent)**: `researcher@local`
- **Temporary Sub-Agent (Temp Worker)**: `coder_tmp_8f2a@local`
- **Agent from Another Instance (Outsourcing/Branch)**: `reviewer@node_tokyo_01`

**Benefits**: By using this addressing standard, the AACP communication protocol **requires no structural changes**. When sending messages, Agents still only need to fill in `sender` and `receiver`. Whether it's superior-subordinate, peer-to-peer, or cross-machine, everyone is an equal node in the eyes of the "bus."

### 2. The "Kernel" Concept: Taking Over the HR Department

Who is responsible for hiring (creating) and firing (destroying) temporary workers? We must not let the main Agent create objects out of thin air, as this leads to memory leaks and ghost processes.

We need a special virtual Agent built into the `Dispatcher` (Central Scheduler) called **`system@local` (or Kernel)**.

We add several system-level `Intents` to the AACP protocol:

- `SPAWN` (Hatch/Create)
- `TERMINATE` (Terminate/Destroy)

**The lifecycle workflow for a temporary worker is as follows:**

1. **Hiring (Creation)**: The main agent `planner@local` realizes it cannot write code, so it sends a message to `system@local` with the Intent `SPAWN` and requirements in the Payload: `{"role": "coder", "type": "temporary", "prompt": "You are a temporary worker proficient in Python"}`.
2. **Onboarding (Registration)**: Upon receiving this, the system dynamically instantiates an `OpenCode Agent`, assigns the ID `coder_tmp_8f2a@local`, registers it in the dispatcher's event loop, and replies to the main Agent: "Your temporary worker is online; here is their ID."
3. **Working (Task Assignment)**: The main Agent sends a `TASK_ASSIGN` message directly to `coder_tmp_8f2a@local`. Once finished, the temporary worker returns a `TASK_COMPLETE` message.
4. **Firing (Destruction)**: Once the code is confirmed, the main Agent sends a `TERMINATE` message to `system@local` (targeting that temp worker's ID). The system unregisters it from the memory queue, and Python's Garbage Collection (GC) automatically clears its occupied memory.

### 3. Decoupling Organizational Relationships: Relying on "Context Pointers" instead of Hardcoding

How do we distinguish between peer-to-peer and superior-subordinate relationships?

**Answer: Logic layer distinguishes them, not the underlying layer.**

On the AegisOS communication bus, there is no physical "you are my subordinate" connection. All constraints are implemented via the **Shared Workspace (Blackboard)** and the `context_pointer` (file pointer) in AACP messages.

- **Peer Collaboration**: A Product Manager finishes `prd.md` and messages a peer Programmer: "I've finished it; go check `_workspace/prd.md`."
- **Superior-Subordinate Collaboration**: A main Agent creates a sub-Agent and messages: "Your task is to read instructions from `_workspace/sub_task_1.json`, write results to `_workspace/result_1.json`, and report only to me."

This protocol- and blackboard-based design allows for infinite scalability of organizational topology.

### 4. Cross-Instance Communication: Remote Branch Collaboration

You mentioned the future need for communication between "main Agents across different instances" (e.g., your mobile instance communicating with a high-performance cloud instance).

With the `xxx@instance_id` addressing mechanism, this problem is solved.

The `Dispatcher` only needs a simple check when routing messages:

```python
if receiver.endswith("@local"):
    # Local routing, directly put message into the corresponding local Agent's memory
    route_to_local_agent(receiver, message)
else:
    # Cross-machine routing, hand message to "Egress Gateway"
    send_to_remote_via_websocket_or_grpc(receiver, message)
```

In this architecture, AegisOS is natively distributed!
