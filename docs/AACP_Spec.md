# AegisOS Agent Collaboration Protocol (AACP) Specification v0.1

AACP 是 AegisOS 内部 Agent 之间通信的标准协议，旨在提供结构化、可追溯且支持跨语言扩展的协作框架。

## 1. 消息模型 (Message Model)

所有消息必须符合 AACP 规格，底层通常序列化为 JSON。

| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `message_id` | UUID | 消息的唯一标识符（自动生成）。 |
| `sender` | URI | 发送者标识，格式：`role_uuid@instance_id`。 |
| `receiver` | URI | 接收者标识，或 `BROADCAST` 表示广播。 |
| `intent` | Enum | 消息意图（见下文）。 |
| `payload` | Dict | 业务数据内容。 |
| `context_pointer` | String | (可选) 指向 Workspace 中的文件路径，用于大数据传递。 |
| `timestamp` | DateTime | 消息创建时间。 |

## 2. 消息意图 (Intents)

- `REQUEST`: 发起一个任务或询问。
- `INFORM`: 单向告知信息或状态更新。
- `REPLY`: 响应之前的 `REQUEST`。
- `SPAWN`: 系统指令，请求创建一个新的子 Agent。
- `TERMINATE`: 系统指令，请求销毁一个 Agent。
- `ERROR`: 报告执行错误。

## 3. 地址规范 (Addressing)

AACP 使用 URI 格式进行寻址：
- **本地 Agent**: `agent_name@local` 或 `agent_name@current_instance_id`
- **远程 Agent**: `agent_name@remote_instance_id`
- **系统代理**: `system@local` (负责生命周期管理)

## 4. 大数据传递规范 (The "Context Pointer" Pattern)

为了避免 Token 消耗和消息队列阻塞，严禁在 `payload` 中传递超过 2KB 的文本或二进制数据。
**标准做法**：
1. 发送者将大数据写入 Workspace (例如 `temp/output.log`)。
2. 消息的 `payload` 仅包含摘要或元数据。
3. 消息的 `context_pointer` 设置为该文件路径。
4. 接收者通过 `WorkspaceManager` 读取该路径。

## 5. 安全准则

- **输入校验**: 接收方必须验证 `payload` 中的参数类型。
- **路径隔离**: `context_pointer` 必须经过 `WorkspaceManager` 的安全校验，严禁包含 `../`。
- **身份验证**: 当前版本假设内部总线受信任，后续版本将引入基于公私钥对的消息签名验证。
