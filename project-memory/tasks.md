# AegisOS Active Tasks (Phase 2 Focus)

## 近期回顾 (Phase 1 归档)
- [x] **内核核心实现**：Dispatcher, Workspace, Protocol, Kernel Agent 已上线。
- [x] **安全性与稳定性**：完成边缘情况单元测试，发布 AACP 协议规格文档。

## 当前重点 (Phase 2: 认知引擎与记忆)
### Task 5: LLM Engine & AACPAgent 集成
- [x] **LLM Engine 实现**：完成 OpenAI/Anthropic 异步适配器。
- [x] **AACPAgent 基类**：实现结构化决策闭环。
- [ ] **异步回调集成**：将 `AACPAgent.handle_message` 真正作为回调函数注册到 `AegisDispatcher` 中。
- [ ] **Prompt 优化**：针对不同模型优化 AACP 响应的稳定性，减少格式幻觉。
- [ ] **Prompt Caching**：利用 API 缓存降低重复指令的成本。

### Task 6: Memory Manager 实现
- [ ] **Hot Memory (滑动窗口)**：
    - [ ] 实现 `MemoryManager.add_message()`。
    - [ ] 实现基于 Token 计数或轮数的自动截断逻辑。
    - [ ] 集成到 `AACPAgent` 替换现有的简单列表历史。
- [ ] **Cold Memory (向量数据库)**：
    - [ ] 集成 ChromaDB 或 Qdrant。
    - [ ] 实现异步 RAG 检索流程。
- [ ] **记忆固化 (Knowledge Distillation)**：
    - [ ] 实现后台任务，自动从热记忆中提取“事实/偏好”存入冷记忆。

### Task 7: 基础安全沙箱
- [ ] **SandboxRunner**：基于受限子进程实现 Python 代码执行隔离。
- [ ] **HITL 拦截器**：定义敏感动作的审批工作流。

---
*注：长期规划请参见 [Roadmap](./roadmap.md)*
