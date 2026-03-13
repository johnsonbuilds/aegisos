# AegisOS Changelog

## [0.1.1] - 2026-03-13
### Added
- **LLM Engines**: 对接 OpenAI (Structured Outputs) 与 Anthropic API 的异步引擎实现。
- **AACP Specification**: 在 `docs/AACP_Spec.md` 中编写了详细的协议规范。
- **Edge Case Tests**: 增强了对 `Dispatcher` 异常隔离和 `Workspace` 安全路径的测试覆盖。
- **Dependencies**: 引入了 `openai` 和 `anthropic` SDK。

### Fixed
- 修复了 `Dispatcher` 在注册/注销时的系统代理保护逻辑。
- 修复了 `WorkspaceManager` 在处理深层目录时的自动创建逻辑。
