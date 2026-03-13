# Roadmap

状态: 进行中

### Phase 1: 内核与本地通信总线 (The Core Kernel)

**阶段目标**：不挂载真实 LLM，纯粹用代码搭建 AegisOS 的“主板”。证明多智能体可以在单机环境下，通过标准协议和共享文件进行动态协作。

- **Task 1.1: 标准化通信协议 (AACP)**
    - 使用 Pydantic v2 定义 AACPMessage，确保所有消息包含 context_pointer（文件指针），从物理上杜绝大段文本直接在总线中传递。
- **Task 1.2: 共享工作区 (Blackboard / WorkspaceManager)**
    - 建立基于本地文件系统的沙盒目录（如 _workspace/{session_id}），实现异步读写，并加入严格的“防路径穿越（Path Traversal）”安全校验。
- **Task 1.3: 核心调度器 (AegisDispatcher) 与内核代理**
    - 基于 asyncio 开发全局消息事件循环。
    - 内置 system@local 内核代理，实现 SPAWN（动态创建子代理/临时工）和 TERMINATE（销毁代理）的生命周期管理。
- **Task 1.4: E2E 协同验证**
    - 使用 Dummy Agent（写死的函数）跑通“产品经理派发任务 -> 创建临时程序员 -> 读写工作区文件 -> 销毁程序员”的全链路。

### Phase 2: 认知引擎与记忆突触 (The Brain & Memory)

**阶段目标**：挂载真实大模型（OpenAI/Claude），并彻底解决传统 Agent（如 OpenClaw）“每次请求耗费 10万+ Token”的致命痛点。

- **Task 2.1: LLM Engine 与结构化输出挂载**
    - 接入大模型 API，强制利用底层模型的 Structured Outputs 能力，保证大模型吐出的任何回复都是严格合规的 AACP JSON 格式，消除“幻觉指令”。
- **Task 2.2: 动态技能路由 (Dynamic Skill Routing)**
    - 引入极小模型（如 Llama-3-8B 级别分类器），在每次主模型执行前，拦截意图，**仅将最相关的 2-3 个技能的 Prompt 挂载到上下文中**，缩减 90% 的上下文占用。
- **Task 2.3: 冷热分离记忆引擎 (Memory Manager)**
    - **热记忆**：实现滑动窗口机制，仅保留近 5 轮对话及当前任务状态大纲。
    - **冷记忆**：后台异步运行小型 Agent，将老旧对话总结为“事实 (Facts)”提取并存入轻量级向量数据库（如 Chroma），通过 RAG 随时唤醒。
- **Task 2.4: 提示词缓存 (Prompt Caching)**
    - 启用 API 层面的系统级缓存，将常驻的系统指令和核心技能缓存，极大降低成本和延迟。

### Phase 3: 零信任沙箱与遗留生态兼容 (The Shield & Ecosystem)

**阶段目标**：让 Agent 能够安全地执行真实代码与动作，同时“合法窃取” OpenClaw 庞大的社区技能市场。

- **Task 3.1: Serverless/容器化沙箱执行器 (SandboxRunner)**
    - 开发安全的执行器环境（初期使用 Python 严格受限的 subprocess，后期平滑升级到 Docker 容器或 Firecracker VM），隔绝宿主机系统。
- **Task 3.2: HITL 细粒度权限拦截器 (Human-in-the-loop)**
    - 在网关层植入拦截器。当 Agent 试图执行“发送邮件”、“提交代码”、“发起网络请求”等敏感动作时，暂停系统，并通过控制台或 IM 工具向人类发送结构化的 [Approve/Deny] 授权卡片。
- **Task 3.3: OpenClaw 兼容层 (Compatibility Layer)**
    - 编写转换器，自动解析 OpenClaw 格式的 skill.md 及 action.py，将其封装为 AegisOS 的原生技能，并在上述的安全沙箱中降级运行，实现首日生态即插即用。

### Phase 4: 生产力重武器与业务流编排 (The Professional Team)

**阶段目标**：将我们在 PRD 中指定的四大开源 AI 神器原生集成到 AegisOS 中，使其具备商业级的生产力；并引入流程化管理。

- **Task 4.1: 集成 OpenCode (专属编程大脑)**
    - 将 OpenCode 封装为标准的 Coder_Agent。当系统需要写代码、自我进化或维护项目时，直接将任务分发给这个专业的编程子代理，在云端沙箱闭环测试代码。
- **Task 4.2: 集成 Firecrawl & Scrapling (视觉与重型数据装甲)**
    - 将 Firecrawl 封装为 Vision_Agent，将网页转为纯净 Markdown，杜绝由于无头浏览器带来的过度耗能和提示词注入风险。
    - 将 Scrapling 封装为 Scraper_Agent，处理需绕过 Cloudflare 盾和需 7x24 小时监控的重型数据任务。
- **Task 4.3: 集成 CLI-Anything (精准动作转译层)**
    - 将 GUI 软件封装为无头的 JSON 命令，彻底抛弃脆弱的鼠标点击模拟操作。
- **Task 4.4: SOP 静态工作流引擎**
    - 支持读取 YAML 格式的 SOP 文件，让主代理（Planner）能够根据固定的企业级标准操作流程来分配和调度多智能体协作。

### Phase 5: 终极网关与 P2P 星状网络 (The Distributed Future)

**阶段目标**：突破单机限制，实现多台设备（手机、PC、云服务器）和不同实体（跨企业协作）的智能体互相通信，完成“操作系统”的终极拼图。

- **Task 5.1: 演进式网关开发 (Egress Gateway)**
    - 在 AegisDispatcher 中加入 URI 解析拦截逻辑（如 xxx@remote_node），将非本地消息转发至独立网关组件。
- **Task 5.2: Go 网络边车开发 (AegisOS-Net Daemon)**
    - 使用 Go 语言与 go-libp2p 库，独立开发一个超轻量（~20MB）的 P2P 网络守护进程。实现 Kademlia DHT 节点寻址、WebRTC 打洞与状态保活。
- **Task 5.3: IPC 跨语言通信桥梁**
    - 在 Python 主进程与 Go 守护进程之间，建立基于本地 Unix Domain Socket (UDS) / localhost gRPC 的通信机制。
- **Task 5.4: CI/CD 一键打包构建系统**
    - 配置自动化流水线，将 Go 源码交叉编译为三大操作系统的可执行文件，并作为静态资源塞入 Python 的 .whl 包中。实现用户执行 pip install aegisos 即获取完整双语引擎的终极无感体验。