# AegisOS Tasks

## 当前任务 (Phase 1 尾声)
- [ ] **完善单元测试**：确保 `Dispatcher` 和 `WorkspaceManager` 的边缘情况得到覆盖。
- [ ] **文档化 AACP 协议**：为开发者编写详细的协议说明文档。

## 下一阶段 (Phase 2 - 大模型与安全)
### Task 5: LLM Engine 挂载
- [ ] 实现 `LLMEngine` 类，对接 OpenAI/Claude API。
- [ ] 封装 Structured Outputs 逻辑，强制 LLM 返回符合 AACP 规格的 JSON。
- [ ] 支持提示词缓存 (Prompt Caching) 以降低成本。

### Task 6: Memory Manager 实现
- [ ] 实现热记忆截断逻辑 (滑动窗口)。
- [ ] 集成向量数据库 (如 ChromaDB/Qdrant) 用于冷记忆存储。
- [ ] 实现异步事实/偏好提取智能体。

### Task 7: 基础安全沙箱
- [ ] 实现 `SandboxRunner`，支持在受限子进程中执行 Python 代码。
- [ ] TODO: 调研轻量级容器 (Docker/Firecracker) 的集成方案。

## 待办事项 (TODO)
- [ ] TODO: 确定冷记忆提取的触发阈值。
- [ ] TODO: 设计 AACP 跨实例路由的具体网关协议。
- [ ] TODO: 评估 WebAssembly 作为本地轻量沙箱的可行性。
