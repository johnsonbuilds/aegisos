# AegisOS 核心骨架 Agent 开发冲刺计划

### 第一阶段（Phase 1）：通信总线与多智能体协同 MVP（纯本地、无 LLM 版）

在这个阶段，我们先不接入任何真实的大模型 API，纯粹用代码逻辑把 AegisOS 的“主板”焊好。

### Task 1: 定义 AACP 通信协议 (Agent-to-Agent Communication Protocol)

- **任务目标**：定义 AegisOS 内部所有组件和 Agent 之间通信的标准数据结构。
- **Agent 指令/Prompt**：
    
    > "你现在的任务是为 AI Agent 操作系统 AegisOS 编写核心通信协议。请使用 [Python的Pydantic / TypeScript的Zod] 定义一个名为 AACPMessage 的数据模型。
    > 
    > 
    > 包含字段：message_id (UUID), timestamp, sender (str), receiver (str), intent (枚举: REQUEST, PROPOSE, INFORM, TASK_COMPLETE, ERROR), payload (字典), context_pointer (可选的字符串，表示文件路径)。
    > 
    > **验收标准**：提供完整的模型代码，并编写一个简单的单测，验证一个标准的 JSON 字符串能否成功被解析为该对象。"
    > 

### Task 2: 实现黑板模式 (Blackboard / Shared Workspace Manager)

- **任务目标**：实现一个基于本地文件系统的共享工作区，让不同 Agent 通过文件指针交换庞大的数据。
- **Agent 指令/Prompt**：
    
    > "请开发一个 WorkspaceManager 类。
    > 
    > 
    > 功能要求：
    > 
    > 1. 初始化时，在项目根目录创建一个 _workspace/{session_id} 的文件夹。
    > 2. 提供 write_file(filename, content) -> filepath 方法。
    > 3. 提供 read_file(filepath) -> content 方法。
    > 4. 提供 list_files() 方法。
    >     
    >     **安全要求**：必须防止路径穿越攻击（Path Traversal），所有读写必须被严格限制在 _workspace/{session_id} 目录内。
    >     
    >     **验收标准**：编写对应的单元测试，证明跨目录读取会抛出异常，正常读写能成功返回内容。"
    >     

### Task 3: 核心调度器 (Central Dispatcher & Event Loop)

- **任务目标**：构建 AegisOS 的“心脏”，负责接收所有 AACP 消息并分发给对应的 Agent。
- **Agent 指令/Prompt**：
    
    > "请开发一个基于内存队列的 AegisDispatcher 调度器。
    > 
    > 
    > 功能要求：
    > 
    > 1. 维护一个已注册 Agent 的列表：register_agent(agent_name, agent_callback)。
    > 2. 拥有一个消息队列和死循环（Event Loop）：从队列中取出 AACPMessage，根据 receiver 字段，调用对应 Agent 的回调函数。如果 receiver 是 'BROADCAST'，则发给所有 Agent。
    >     
    >     **验收标准**：写一个测试脚本，注册 Agent A 和 Agent B，让 Dispatcher 成功把 A 发出的消息路由并触发 B 的回调函数。"
    >     

### Task 4: 完成 Dummy Agent 的端到端协同测试 (E2E Test)

- **任务目标**：串联 Task 1, 2, 3，完成我们在上一次对话中提到的“假装是产品经理”和“假装是程序员”的协同工作验证。
- **Agent 指令/Prompt**：
    
    > "基于已有的 AACPMessage, WorkspaceManager 和 AegisDispatcher，编写一个端到端测试脚本 test_e2e_collaboration.py。
    > 
    > 1. 创建 Dummy PM Agent：被唤醒后，向 workspace 写入 req.txt（内容：“写一个计算器”），然后向 Dispatcher 发送一条发给 Coder 的 TASK_COMPLETE 消息，携带 pointer req.txt。
    > 2. 创建 Dummy Coder Agent：收到消息后，读取 pointer 对应的 req.txt，然后在 workspace 生成 code.py（随便写个 print），并向 PM 发送 INFORM 消息说搞定了。
    >     
    >     **验收标准**：一键运行该脚本，能在终端打印出完美的 AACP 通信日志，并在 _workspace 里看到正确生成的两个文件。"
    >     

---

### 第二阶段（Phase 2）：真实大模型挂载与安全沙箱初步（视 Phase 1 完成情况开启）

当第一阶段的 4 个 Task 被 AI Agent 完美敲完且测试通过后，AegisOS 的底层骨架就已经立住了。接下来你可以继续派发第二阶段任务：

- **Task 5 (LLM 挂载)**：开发 LLMEngine，对接 OpenAI / Claude 的 API。关键要求是强制 LLM 必须输出符合 AACP 协议的 JSON 格式（使用 Structured Outputs），而不是闲聊废话。
- **Task 6 (Token 路由拦截)**：根据 PRD 4.2，开发 MemoryManager。在组装 LLM 的 Prompt 时，强制执行：保留最新 5 轮对话，超过部分截断，并只注入所需的 2-3 个技能描述。
- **Task 7 (技能沙箱)**：基于 Python 的 subprocess 或轻量级 Docker SDK，写一个 SandboxRunner，用来安全执行第三方代码，限制其网络和文件权限。