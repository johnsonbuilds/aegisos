# AegisOS Roadmap

## 第一阶段 (Phase 1): 核心骨架与 MVP (已基本完成)
**目标**：构建 AegisOS 的“主板”，实现基础通信总线与多智能体协同。

- [x] **AACP 通信协议定义**：基于 Pydantic 的标准化消息模型。
- [x] **WorkspaceManager (黑板系统)**：实现基于文件的共享工作区，具备路径穿越防御功能。
- [x] **AegisDispatcher (核心调度器)**：基于 asyncio 的异步事件循环，支持消息路由与广播。
- [x] **Kernel 系统代理**：支持动态生命周期管理 (SPAWN/TERMINATE)。
- [x] **E2E 协同验证**：Dummy Agent 自动化任务交付流程测试。

## 第二阶段 (Phase 2): 大模型挂载与安全增强 (当前阶段)
**目标**：赋予 AegisOS “大脑”，并建立初步的安全隔离。

- [ ] **LLM Engine 挂载**：对接 OpenAI/Claude API，强制 Structured Outputs (JSON)。
- [ ] **MemoryManager (记忆引擎)**：实现冷热记忆分离机制 (Facts/Preferences 提取 + RAG)。
- [ ] **Dynamic Skill Routing**：意图分类器，根据任务动态挂载技能说明以节省 Token。
- [ ] **SandboxRunner (技能沙箱)**：基于 subprocess 或轻量级 Docker 的初步隔离执行环境。

## 第三阶段 (Phase 3): 生产力模块集成
**目标**：引入重型业务组件，支持 7x24 小时稳定运行。

- [ ] **CLI-Anything 动作转译层**：将 GUI 软件封装为确定性 JSON 接口。
- [ ] **OpenCode 编程大脑**：负责云端沙箱中的技能生成与自进化。
- [ ] **Firecrawl 安全视觉**：纯净 Markdown 网页采集。
- [ ] **Scrapling 数据采集装甲**：高强度反爬与 UI 自适应爬虫。

## 第四阶段 (Phase 4): 基础设施化与分布式
**目标**：性能优化、跨机器协同与去中心化寻址。

- [ ] **AegisOS-Net (Go Sidecar)**：基于 `go-libp2p` 实现 P2P 网络栈，支持 Kademlia DHT 寻址。
- [ ] **Evolutionary Egress Gateway**：
    - [ ] 阶段 1：支持 Tailscale 虚拟局域网路由。
    - [ ] 阶段 2：集成 Nostr Relay 实现跨防火墙公钥路由。
    - [ ] 阶段 3：全量开启 Libp2p/WebRTC 打洞。
- [ ] **IPC 通信优化**：实现 Python 与 Go 之间的 Unix Domain Socket / gRPC 高速通道。
- [ ] **CI/CD 二进制捆绑**：交叉编译 Go 引擎并打入 Python Wheel 包。
- [ ] **SOP 工作流引擎**：支持基于 YAML 的复杂标准作业流程定义。
