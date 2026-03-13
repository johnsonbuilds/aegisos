# AegisOS Changelog

## [0.1.2] - 2026-03-13
### Added
- **Dynamic Spawning**: `AegisDispatcher` (system@local) 现在支持通过 `SPAWN` 意图动态实例化 `AACPAgent`。
- **Lifecycle Integration**: 实现了 “SPAWN -> WORK -> TERMINATE” 的完整智能体生命周期闭环。
- **NOOP Mechanism**: 在 `AACPResponse` 中引入了可选的 `receiver` 机制，允许 Agent 通过不发送消息来打破无限循环。
- **Integration Tests**: 新增 `tests/test_aacp_integration.py` 验证多智能体动态协作流程。

### Changed
- **AACPAgent Refactor**: 优化了 `__init__` 签名，支持基于角色和 UUID 自动生成 URI。
- **Auto-Reaction**: `AACPAgent` 现在会在收到消息后通过 `handle_message` 自动触发思考动作。

## [0.1.1] - 2026-03-13

### Fixed
- 修复了 `Dispatcher` 在注册/注销时的系统代理保护逻辑。
- 修复了 `WorkspaceManager` 在处理深层目录时的自动创建逻辑。
