# AegisOS Changelog

## [0.1.0] - 2026-03-11
### Added
- **Core Skeleton**: 实现了 AegisOS 的核心骨架。
- **AACP Protocol**: 基于 Pydantic 定义了 Agent 间通信协议模型。
- **AegisDispatcher**: 实现了基于 asyncio 的中心消息分发器，支持 Agent 注册与消息路由。
- **WorkspaceManager**: 实现了具备安全校验的共享工作区管理，支持文件的异步读写。
- **Kernel Agent**: 内置系统代理，支持动态 `SPAWN` 和 `TERMINATE` 生命周期管理。
- **E2E Test**: 完成了端到端的 Dummy Agent 动态生命周期与协同测试脚本。
- **Project Memory**: 建立了标准的项目记忆系统文档结构。

### Documentation
- 完成产品需求文档 (PRD)。
- 完成演进式架构设计方案。
- 完成 Agent 分工协作架构设计。
- 完成第一阶段开发冲刺计划。
