# AegisOS Technical Decisions

## 1. 通信架构：协议化 vs 自然语言
- **决策**：采用标准化 JSON 协议 (AACP) 结合黑板模式，而非 Agent 间的纯自然语言对话。
- **理由**：
  - 降低 Token 消耗：通过指针传递大文件路径，避免重复读取。
  - 确定性：JSON 结构便于程序处理，减少解析歧义。
  - 可观测性：消息日志清晰反映系统执行流程。

## 2. 安全策略：零信任沙箱
- **决策**：彻底放弃本地 Root 权限，所有 Skills 必须在云端 WebAssembly 或 Firecracker VM 等沙箱中运行。
- **理由**：
  - 防止提示词注入攻击导致的主机失控。
  - 实现用完即毁，隔离技能执行产生的副作用。

## 3. 交互方式：API/CLI vs GUI 自动化
- **决策**：优先集成 CLI 工具并进行动作转译 (CLI-Anything)，放弃脆弱且高耗能的视觉模型点击模拟。
- **理由**：
  - 提高稳定性：CLI 输出具备确定性结果。
  - 降低延迟：API 交互远快于无头浏览器渲染。

## 4. 记忆管理：冷热分离
- **决策**：
  - **热记忆 (RAM)**：仅保留最近 5 轮对话及状态大纲。
  - **冷记忆 (硬盘)**：异步提取事实 (Facts) 与偏好 (Preferences) 存入向量数据库 (Vector DB)。
- **理由**：解决长对话 Token 爆炸问题，实现无限上下文支持。

## 5. 开发范式：异步原生 (Async-First)
- **决策**：全系统基于 `asyncio` 构建，抛弃传统多线程。
- **理由**：高效处理 Agent 等待 LLM 返回及大量文件 I/O 密集型任务，降低系统资源开销。

## 6. 项目结构：Standard src-layout
- **决策**：强制采用 `src/aegisos/` 的顶级命名空间结构，测试代码放在 `tests/` 目录。
- **理由**：
  - 抢占唯一顶级命名空间，彻底杜绝 `core`、`agents` 等常见目录名引发的第三方包导入冲突（命名空间污染）。
  - 顺应现代 Python 构建工具（如 uv）的最佳实践，确保本地测试环境与最终打包安装的生产环境行为一致。

## 7. 混合架构：Python AI 逻辑 + Go 网络 Sidecar
- **决策**：主进程使用 Python 处理 Agent 调度与 AI 逻辑，底层 P2P 网络栈使用 Go (基于 `go-libp2p`) 实现并作为 Sidecar 进程运行。
- **理由**：
  - **性能**：Go 语言处理高并发 P2P 状态机、DHT 寻址及 NAT 打洞比 Python 更稳定且资源占用更低。
  - **生态**：`libp2p` 在 Go 语言中的成熟度远高于 Python 社区。

## 8. 部署策略：预编译二进制捆绑 (Binary Bundling)
- **决策**：将交叉编译后的 Go 二进制文件直接打包进 Python Wheel 包的 `bin/` 目录。
- **理由**：
  - **无感体验**：用户通过 `uv add aegisos` 或 `pip install` 即可获得完整的跨机器协同能力，无需手动安装 Go 环境或配置复杂的 P2P 节点。
  - **进程管理**：Python 启动器会自动根据平台拉起对应的 Sidecar 进程，并负责其生命周期管理。

## 9. 智能体行为：自主反应与 NOOP 机制
- **决策**：
  - `AACPAgent` 在收到消息后通过 `handle_message` 自动触发 `think()` 循环。
  - `AACPResponse.receiver` 可为 `None`，代表 Agent 决定不采取进一步行动 (NOOP)。
- **理由**：
  - **自主性**：减少显式的 `think` 调用代码，使 Agent 具备原生反应力。
  - **防死循环**：通过显式的 NOOP 状态打破 Agent 与自身或他人的无限消息循环。

## 10. 系统内核：动态孵化 (Dynamic Spawning)
- **决策**：`AegisDispatcher` 中的 `system@local` 代理通过 `SPAWN` 意图动态实例化 Agent 类，而非仅注册简单的回调函数。
- **理由**：
  - **对象化管理**：确保所有被孵化的 Agent 都具备完整的认知与记忆管理能力，而非孤立的函数。
  - **生命周期闭环**：配合 `TERMINATE` 意图，实现 Agent 的自动化入职与销毁流程。

## 11. Agent 架构：协议 (Protocol) vs. 实现 (Class)
- **决策**：坚持“协议优先”原则。任何符合 AACP 协议（能收发 AACPMessage）的实体在 AegisOS 视角下均视为 Agent。
- **理由**：
  - **多态性**：系统必须支持多种类型的实现，而不仅仅是 LLM 驱动。
  - **效率与成本 (Efficiency & Cost)**：引入功能型 Agent (Stub/Functional) 处理高频系统任务（如监控、心跳），无需消耗 Token 且低延迟。
  - **确定性与安全 (Determinism & Safety)**：关键系统路径（如资源销毁）应由逻辑确定的功能型 Agent 执行。
  - **异构集成 (Heterogeneity)**：为未来 Phase 5 的 Go-Sidecar 跨语言通信奠定基础。

## 12. 资源解耦：引入 AgentFactory
- **决策**：将 Agent 实例化逻辑从 `AegisDispatcher` 中抽离，移至独立的 `AgentFactory`。
- **理由**：
  - **解耦内核**：Dispatcher 仅负责消息路由，Factory 负责对象构建，符合开闭原则 (Open-Closed Principle)。
  - **动态扩展**：允许在运行时注册新的 Agent 类型，而无需修改 Dispatcher 核心代码。


