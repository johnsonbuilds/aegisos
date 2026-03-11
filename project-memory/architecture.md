# AegisOS Architecture

## 1. 系统分层
- **Control Plane (控制面)**：负责消息总线 (AegisDispatcher)、Agent 寻址、生命周期管理和系统安全拦截。
- **Agent Plane (智能体面)**：运行具体的 Agent 逻辑、LLM 交互层以及执行特定任务的 Skills。
- **Data Plane (数据面/工作区)**：共享工作区 (Blackboard System)，通过文件系统管理 Agent 间共享的大规模数据。

## 2. 核心组件
### 2.1 AegisDispatcher (核心调度器)
- 基于 `asyncio.Queue` 的异步消息路由。
- 维护全局注册表，支持 `system@local` 内核代理。
- 处理 AACP 消息的路由与广播。

### 2.2 WorkspaceManager (黑板模式管理器)
- 负责 `_workspace/{session_id}` 的目录生命周期。
- 提供 `write_file` / `read_file` 异步接口。
- **安全性**：内置路径穿越校验，确保所有 I/O 局限于工作区内。

### 2.3 AACP (Agent-to-Agent Communication Protocol)
- **格式**：JSON (Pydantic 模型)。
- **字段**：`message_id`, `timestamp`, `sender`, `receiver`, `intent`, `payload`, `context_pointer`。
- **意图(Intent)**：REQUEST, PROPOSE, INFORM, TASK_COMPLETE, ERROR, SPAWN, TERMINATE。

## 3. 寻址与协同机制
### 3.1 Agent URI
采用类似邮箱的寻址标准：`{role}_{uuid}@{instance_id}`。
- 示例：`planner@local`, `coder_tmp_8f2a@local`。

### 3.2 共享工作区指针 (Context Pointer)
Agent 之间不传递大型数据块，而是通过 AACP 消息中的 `context_pointer` 传递工作区内的文件相对路径。

### 3.3 动态生命周期 (Kernel Control)
主代理通过向 `system@local` 发送 SPAWN/TERMINATE 消息来动态创建和销毁临时子代理，实现资源的按需分配。

## 4. 技术栈
- **核心语言**：Python 3.11+
- **包管理**：uv
- **异步框架**：asyncio / aiofiles
- **数据校验**：Pydantic v2
