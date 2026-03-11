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

### 2.4 OpenClaw Compatibility Layer (兼容层)
- 负责自动解析 OpenClaw 的第三方 `skill.md` 市场生态。
- **安全降级**：加载的外部代码强制注入云端 Serverless 沙箱或 Docker 容器执行，确保首日生态即插即用。

## 3. 寻址与协同机制
### 3.1 Agent URI
采用类似邮箱的寻址标准：`{role}_{uuid}@{instance_id}`。
- 示例：`planner@local`, `coder_tmp_8f2a@local`。

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

## 4. 关键能力引擎 (Engines)
AegisOS 通过集成专业化引擎扩展其能力：
- **CLI-Anything (动作转译层)**：将开源 GUI 软件封装为具备确定性 JSON 输出的 CLI 工具。
- **OpenCode (编程大脑)**：云端沙箱中的独立编程智能体，负责生成、校验和测试新技能代码。
- **Firecrawl (安全视觉与阅读)**：替代高耗能浏览器，获取纯净 Markdown 或结构化数据。
- **Scrapling (数据采集装甲)**：极强适应性的爬虫框架，绕过反爬机制并适应 UI 更新。

## 5. 技术栈
- **核心语言**：Python 3.11+
- **包管理**：uv
- **异步框架**：asyncio / aiofiles
- **数据校验**：Pydantic v2
