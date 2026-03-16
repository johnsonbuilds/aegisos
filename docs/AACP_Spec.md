# AegisOS Agent Collaboration Protocol (AACP) Specification v0.1

AACP is the standard communication protocol between Agents within AegisOS, designed to provide a structured, traceable, and cross-language extensible collaboration framework.

## 1. Message Model

All messages must comply with the AACP specification, typically serialized as JSON.

| Field | Type | Description |
| :--- | :--- | :--- |
| `message_id` | UUID | Unique identifier for the message (auto-generated). |
| `sender` | URI | Sender identifier, format: `role_uuid@instance_id`. |
| `receiver` | URI | Receiver identifier, or `BROADCAST` for broadcasting. |
| `intent` | Enum | Message intent (see below). |
| `payload` | Dict | Business data content. |
| `context_pointer` | String | (Optional) File path in the Workspace for large data transfer. |
| `timestamp` | DateTime | Message creation time. |

## 2. Intents

- `REQUEST`: Initiate a task or inquiry.
- `INFORM`: One-way notification of information or status update.
- `REPLY`: Response to a previous `REQUEST`.
- `SPAWN`: System instruction to create a new sub-Agent.
- `TERMINATE`: System instruction to destroy an Agent.
- `ERROR`: Report an execution error.

## 3. Addressing

AACP uses URI format for addressing:
- **Local Agent**: `agent_name@local` or `agent_name@current_instance_id`
- **Remote Agent**: `agent_name@remote_instance_id`
- **System Agent**: `system@local` (responsible for lifecycle management)

## 4. Large Data Transfer (The "Context Pointer" Pattern)

To avoid Token consumption and message queue congestion, it is strictly forbidden to pass text or binary data exceeding 2KB in the `payload`.
**Standard Practice**:
1. The sender writes large data to the Workspace (e.g., `temp/output.log`).
2. The message `payload` contains only a summary or metadata.
3. The `context_pointer` of the message is set to that file path.
4. The receiver reads the path via `WorkspaceManager`.

## 5. Security Guidelines

- **Input Validation**: The receiver must validate the parameter types in the `payload`.
- **Path Isolation**: `context_pointer` must undergo security validation by `WorkspaceManager`, strictly forbidding `../`.
- **Authentication**: The current version assumes the internal bus is trusted; subsequent versions will introduce message signature verification based on public-private key pairs.
