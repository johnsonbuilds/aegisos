# AegisOS 开发约定 (Project Conventions)

本文档记录了 AegisOS 的核心架构设计、工程实践及开发流程，旨在为 AI Agent 的自动化开发提供一致性的指导。

## 1. 核心架构与技术栈

- **包管理**: 强制使用 `uv`。所有依赖添加必须通过 `uv add`。
- **项目结构**: 遵循 **Standard src-layout**。
  - `src/aegisos/`: 源码主目录。
  - `tests/`: 单元测试目录。
  - `scripts/`: 端到端（E2E）或工具脚本。
- **编程模型**: **100% 异步 (async/await)**。所有 I/O、消息分发及 Agent 回调必须定义为 `async def`。
- **数据模型**: 强制使用 **Pydantic V2** (`BaseModel`, `ConfigDict`) 进行所有 AACP 协议和配置的定义。
- **路径安全**: 所有文件系统操作必须经过 `WorkspaceManager` 的路径穿越（Path Traversal）校验。

## 2. 开发生命周期 (Workflow)

对于每个 Phase 的任务，遵循以下循环：

1.  **Research**: 阅读相关 `docs/` 文档，理解任务需求。
2.  **Plan**: 明确实现细节、接口定义及测试策略。
3.  **Act**: 编写/修改代码。
4.  **Validate**: 
    - 运行针对性的单元测试: `pytest tests/test_xxx.py`
    - 运行阶段性 E2E 脚本: `python scripts/test_e2e_xxx.py`
5.  **Commit**: 验证无误后，提交代码并总结当前 Phase。
    - 提交信息格式: `feat(phaseX): description` 或 `fix(component): description`。

## 3. 模块职责划分

- `core.protocol`: 定义 AACP 通信协议的标准格式。
- `core.dispatcher`: 实现基于 `asyncio.Queue` 的消息分发中心。
- `core.workspace`: 管理 Session 隔离的安全文件存储区（Blackboard）。
- `agents/`: 存放各类型 Agent 的实现逻辑。
- `memory/`: (待开发) 处理 Token 路由拦截及长短期记忆。

## 4. 关键接口约定

- **AACP 消息**: 包含 `message_id`, `sender`, `receiver`, `intent`, `payload`, `context_pointer`。
- **Agent 回调**: 签名必须为 `async def callback(message: AACPMessage) -> None`。
- **广播地址**: `BROADCAST` 用于向所有已注册 Agent 发送通知。

---
*本文件将随着项目进度的推进而持续更新。*
