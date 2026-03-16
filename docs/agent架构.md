从工程实现和系统演进（Evolutionary
  Architecture）的角度，引入“不同类型的
  Agent”通常有以下三个核心价值和意义：


  A. 认知成本与资源效率 (Efficiency)
   * AACPAgent (Heavy)：每一轮对话、每一个动作都需要调用
     LLM。这不仅有昂贵的 Token 成本，还有极高的 延迟
     (Latency)。
   * Stub/Functional Agent
     (Light)：有些任务是确定的、重复的。比如一个
     FileWatcherAgent（监控文件变化）或者
     LinterAgent（专门运行代码检查）。让 LLM
     去“思考”如何运行 ls 是极其浪费资源的。
   * 结论：在 AegisOS 中，我们需要“内核态”的快速代理（System
     Daemons）和“用户态”的智能代理（LLM Agents）。


  B. 确定性与安全性 (Determinism & Safety)
   * LLM 具有概率性。即使 Prompt
     写得再好，它也有可能在关键环节（如删除数据库、发送邮件
     ）产生幻觉。
   * Functional Agent 通过硬编码逻辑确保了在关键系统路径上的
     100% 确定性。


  C. 跨语言与异构集成 (Heterogeneity)
   * 我们的 RoadMap (Phase 5) 提到了 Go-Sidecar。
   * 如果一个 Agent 是用 Go 编写的高性能网络网关，它在
     Python 端表现出的就是一个 ProxyAgent 类。它不需要 LLM
     引擎，它只需要把 AACP 消息透传给 Go 进程。