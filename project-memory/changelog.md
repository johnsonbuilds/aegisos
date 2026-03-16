# AegisOS Changelog

## [0.1.3] - 2026-03-16
### Added
- **Standard Actions**: 引入 `src/aegisos/core/actions.py`，定义了标准动作枚举 `AACPAction`（如 `core.exec.code`, `core.fs.read` 等）。
- **Action Payload Schema**: 为标准动作引入了 Pydantic 校验基类 `ActionPayload`。

### Changed
- **AACP Protocol Refactor**: 
    - 移除了 `AACPIntent` 中不合理的 `CODE_EXEC` 和 `CODE_RESULT`。
    - 坚持“协议原语与业务负载解耦”原则。
- **AACPAgent Intelligence Upgrade**: 
    - `AACPResponse` 现在支持 `action` 字段。
    - 实现了 `action` 到 `payload["action"]` 的自动注入机制。
    - 重构了 `Reflexion` 自反思逻辑，使其基于标准 `REQUEST` + `AACPAction.CODE_EXEC` 触发。

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
