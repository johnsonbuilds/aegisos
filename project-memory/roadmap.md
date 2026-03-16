# AegisOS Roadmap

## 第一阶段 (Phase 1): 内核与本地通信总线 (The Core Kernel) (已基本完成)
**目标**：构建 AegisOS 的“主板”，实现标准协议下的多智能体动态协作。

- [x] **AACP 通信协议定义**：基于 Pydantic v2 定义 AACPMessage，强制使用 `context_pointer` 避免大段文本传递。
- [x] **WorkspaceManager (黑板系统)**：实现基于本地文件系统的共享工作区，具备严格的路径穿越防御功能。
- [x] **AegisDispatcher (核心调度器)**：基于 asyncio 的异步事件循环，支持消息路由、广播与生命周期管理。
- [x] **Kernel 系统代理**：实现 `system@local` 内核代理，支持 SPAWN/TERMINATE 动态管理。
- [x] **E2E 协同验证**：Dummy Agent 跑通“任务派发 -> 动态创建 -> 文件读写 -> 销毁”的全链路测试。

## 第二阶段 (Phase 2): 认知引擎与记忆突触 (The Brain & Memory) (当前阶段)
**目标**：挂载真实大模型 (LLM)，并解决 Token 消耗与上下文管理的痛点。

- [ ] **LLM Engine 挂载**：对接 OpenAI/Claude API，强制 Structured Outputs 能力，消除幻觉指令。
- [ ] **MemoryManager (记忆引擎)**：
    - [ ] **热记忆**：实现滑动窗口机制，保留近 5 轮对话及当前任务状态。
    - [ ] **冷记忆**：异步提取“事实 (Facts)”存入轻量级向量库 (Chroma)，通过 RAG 唤醒。
- [ ] **Dynamic Skill Routing**：引入小型分类器 ，拦截意图并仅挂载最相关的 2-3 个技能 Prompt。
- [ ] **Prompt Caching**：启用 API 层面的系统级缓存，降低常驻指令的延迟与成本。

## 第三阶段 (Phase 3): 零信任沙箱与遗留生态兼容 (The Shield & Ecosystem)
**目标**：确保代码执行安全，并“合法窃取” OpenClaw 庞大的社区技能市场。

- [ ] **SandboxRunner (安全沙箱)**：初期使用受限 subprocess，后期升级为 Docker 或 Firecracker 容器。
- [ ] **HITL 细粒度权限拦截器**：敏感动作（发邮件、提代码、连外网）触发 [Approve/Deny] 授权卡片。
- [ ] **OpenClaw 兼容层**：自动解析 OpenClaw 的 `skill.md` 与 `action.py`，实现首日生态即插即用。

## 第四阶段 (Phase 4): 生产力重武器与业务流编排 (The Professional Team)
**目标**：集成开源 AI 神器，具备商业级生产力。

- [ ] **OpenCode 编程大脑**：封装为 Coder_Agent，在云端沙箱闭环测试并维护项目代码。
- [ ] **Firecrawl & Scrapling 数据装甲**：视觉化网页转 Markdown 与重型反爬虫采集集成。
- [ ] **CLI-Anything 动作转译层**：将 GUI 软件封装为无头的 JSON 命令。
- [ ] **SOP 静态工作流引擎**：支持读取 YAML 格式的 SOP 文件，由 Planner 分配标准协作流程。

## 第五阶段 (Phase 5): 终极网关与 P2P 星状网络 (The Distributed Future)
**目标**：突破单机限制，实现跨设备、跨实体的分布式协同。

- [ ] **演进式网关开发 (Egress Gateway)**：
    - [ ] **Phase 5.1**：URI 解析拦截与 Tailscale 虚拟局域网路由。
    - [ ] **Phase 5.2**：集成 Nostr Relay 实现跨防火墙的公钥路由。
    - [ ] **Phase 5.3**：全量开启 Libp2p/WebRTC P2P 打洞。
- [ ] **AegisOS-Net (Go Sidecar)**：基于 `go-libp2p` 独立开发轻量级网络守护进程，实现 DHT 寻址。
- [ ] **IPC 通信优化**：建立基于 Unix Domain Socket / gRPC 的高性能跨语言通信桥梁。
- [ ] **CI/CD 一键打包系统**：交叉编译 Go 引擎并作为静态资源塞入 Python Wheel 包。
