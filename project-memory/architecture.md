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

### 2.2 Evolutionary Egress Gateway (演进式网关)
- **抽象层**：在 `AegisDispatcher` 中抽象出 `Network Gateway`，对上层 Agent 屏蔽底层网络寻址细节。
- **演进阶段**：
  - **阶段 1 (Private Cloud)**：基于 Tailscale/WireGuard 的虚拟局域网路由，利用固定虚拟 IP 进行通信。
  - **阶段 2 (Federated Relay)**：基于 WebSocket + Pub/Sub Relay（类似 Nostr 协议），通过公钥加密消息并由中继站转发，解决跨防火墙穿透。
  - **阶段 3 (Pure P2P)**：基于 Libp2p/DHT 的全去中心化网络，实现 Web3 级的点对点连接。

### 2.3 WorkspaceManager (黑板模式管理器)
- 负责 `_workspace/{session_id}` 的目录生命周期。
- 提供 `write_file` / `read_file` 异步接口。
- **安全性**：内置路径穿越校验，确保所有 I/O 局限于工作区内。

### 2.4 AACP (Agent-to-Agent Communication Protocol)
- **格式**：JSON (Pydantic 模型)。
- **字段**：`message_id`, `timestamp`, `sender`, `receiver`, `intent`, `payload`, `context_pointer`。
- **意图(Intent)**：REQUEST, PROPOSE, INFORM, TASK_COMPLETE, ERROR, SPAWN, TERMINATE。

### 2.5 OpenClaw Compatibility Layer (兼容层)
- 负责自动解析 OpenClaw 的第三方 `skill.md` 市场生态。
- **安全降级**：加载的外部代码强制注入云端 Serverless 沙箱或 Docker 容器执行，确保首日生态即插即用。

## 3. 寻址与协同机制
### 3.1 Agent URI
采用类似邮箱的寻址标准：`{role}_{uuid}@{instance_id}`。
- **本地地址**：`planner@local`。
- **远程地址**：`planner@macbook-pro.local` (Tailscale) 或 `planner@{public_key}` (Nostr/P2P)。

### 3.2 共享工作区指针 (Context Pointer)
Agent 之间不传递大型数据块，而是通过 AACP 消息中的 `context_pointer` 传递工作区内的文件相对路径。

### 3.3 动态生命周期 (Kernel Control)
主代理通过向 `system@local` 发送 SPAWN/TERMINATE 消息来动态创建和销毁临时子代理，实现资源的按需分配。

### 3.4 SOP Workflow (标准作业流程)
- 除了动态创建代理，系统还支持读取 YAML 格式的 SOP 文件，作为多 Agent 协作流的静态骨架。
- 定义环节、分发规则以及打回机制（如：需求 -> 编码 -> 测试 -> 失败打回）。

### 3.5 动态技能路由 (Dynamic Skill Routing)
- 使用极小模型（如 Llama-3-8B）对意图进行实时分类。
- 每次请求仅在主模型 Prompt 中挂载最相关的 2-3 个技能说明，缩减 90% 的上下文占用。
- 全面启用底层模型 API 的 Prompt Caching。

### 3.6 跨进程通信 (IPC via UDS/gRPC)
- **Sidecar 模式**：Python 主进程负责 AI 逻辑与调度，Go 守护进程 (`aegisos-net`) 负责底层 Libp2p 网络与 DHT 寻址。
- **低延迟桥梁**：两者通过本地 **Unix Domain Socket (UDS)** 或 **localhost gRPC** 进行高速通信。
- **流程**：Python 侧将远程消息投递给本地 Socket -> Go 进程解析并路由至全球网络。

## 4. 关键能力引擎 (Engines)
AegisOS 通过集成专业化引擎扩展其能力：
- **CLI-Anything (动作转译层)**：将开源 GUI 软件封装为具备确定性 JSON 输出的 CLI 工具。
- **OpenCode (编程大脑)**：云端沙箱中的独立编程智能体，负责生成、校验和测试新技能代码。
- **Firecrawl (安全视觉与阅读)**：替代高耗能浏览器，获取纯净 Markdown 或结构化数据。
- **Scrapling (数据采集装甲)**：极强适应性的爬虫框架，绕过反爬机制并适应 UI 更新。

## 5. 认知智能体架构映射 (Cognitive Architecture Mapping)
这是 AegisOS 区别于普通脚本的核心灵魂，将 AI 核心范式转化为物理组件映射。

### 5.1 任务拆解与规划 (Task Decomposition / Plan-and-Solve)
- **理论映射**：放弃在 LLM 内存窗口中维护庞大的 Todo List，强制映射到**共享工作区 (Blackboard)** 和 **SOP 引擎**。
- **实现规范**：主代理必须将拆解的子任务物化为物理文件（如 `_workspace/plan.json`），通过 AACP 消息的 `context_pointer` 派发任务。这使得规划过程持久化且支持多 Agent 异步协同。

### 5.2 ReAct 边思考边行动范式 (Reasoning + Acting)
- **理论映射**：放弃传统的 while 单线程死循环，彻底映射到 **AegisDispatcher (核心调度器)** 和 **AACP 通信总线**。
- **实现规范**：Agent 的“思考(Thought)”在内部完成；“行动(Action)”体现为发出带有特定 Intent 的 AACP 消息；“观察(Observation)”体现为通过 Dispatcher 接收目标节点（如 CLI-Anything 插件）返回的执行结果消息。这实现了系统级的 ReAct 解耦。

### 5.3 反思与纠错机制 (Reflexion & Self-Correction)
- **理论映射**：系统级崩溃拦截，映射到 **SandboxRunner (安全沙箱)** 与 **AACP 的 ERROR 意图**。
- **实现规范**：当专属编程代理 (OpenCode) 生成的代码在沙箱中运行崩溃时，绝不允许 AegisOS 宕机。沙箱必须将 Error Traceback 封装为 AACP ERROR 消息发回给代理，触发代理内部的反思提示词，使其自动修复代码并重试。

### 5.4 状态追踪与停止条件 (State Tracking & Final Verification)
- **理论映射**：映射到 **Kernel 系统代理 (system@local)** 和 **生命周期管理**。
- **实现规范**：当子任务完成，必须发出 `TASK_COMPLETE` 消息。主代理通过工作区进行结果验收 (Critic)；验收合格后，主代理必须向系统代理发送 `TERMINATE` 指令，优雅地销毁临时子代理，释放系统资源。

## 6. 技术栈
- **核心语言**：Python 3.11+
- **包管理**：uv
- **异步框架**：asyncio / aiofiles
- **数据校验**：Pydantic v2

## 7. 存储与记忆协作模型 (Storage & Memory Collaboration)
AegisOS 采用“办公桌 + 大脑”的双重存储模型，明确划分了 `WorkspaceManager` 与 `MemoryManager` 的职责边界：

### 7.1 WorkspaceManager (办公桌 / 外部硬盘)
- **定位**：管理**持久化的数据资产 (Artifacts)** 和 **多智能体共享环境 (Blackboard)**。
- **职责**：
    - **大数据处理**：存储 LLM 无法直接放入上下文的大型文件（需求文档、源代码、数据集）。
    - **交付物管理**：记录 Agent 生成的最终产出（代码文件、报告、图片）。
    - **安全隔离**：提供基于 Session 的路径穿越防护，确保 Agent 仅能在授权的工作区内操作。
- **协作方式**：通过 AACP 消息中的 `context_pointer` 传递文件路径。

### 7.2 MemoryManager (大脑 / 认知缓存)
- **定位**：管理**认知的连续性**、**会话上下文**以及 **Token 窗口安全**。
- **职责**：
    - **热记忆 (Hot Memory)**：维护最近的对话历史 (Dialogue) 和思考过程 (Chain of Thought)，实现自动截断与 Token 优化。
    - **冷记忆 (Cold Memory)**：异步提取关键事实 (Facts) 与偏好 (Preferences) 存入向量数据库，实现长期知识沉淀。
    - **认知过滤**：在发送给 LLM 前，根据任务相关性对历史进行重构或压缩（Summarization）。
- **协作方式**：直接挂载在 `AACPAgent` 实例中，作为其推理的上下文来源。

