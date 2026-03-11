# agent分工协作的架构设计


我们需要为AegisOS设计前瞻性的业务场景，在传统软件里，功能是静态写死的；而在我们构想的 AegisOS 中，**智能体不仅是“执行者”，还能成为“管理者”和“造物主”**。这非常像 Linux 系统中的进程管理机制（主进程 fork 出子进程，处理完任务后 kill 掉，彼此通过 IPC 进行进程间通信）。

为了完美支持**“平级协同、动态父子层级、临时工销毁、以及跨机房通信”**，我们需要对 AegisOS 的底层设计进行以下 **4 个维度的架构升级**。你可以将这套设计方案直接融入我们的产品中：

### 1. 统一寻址系统 (Agent URI)：就像给员工发“企业邮箱”

既然要支持这么多复杂的沟通（主从、平级、跨实例），我们就不能只用简单的名字（如 "Coder"）来称呼 Agent。我们需要引入 **Agent URI（统一资源标识符）** 机制。

所有 Agent 的 ID 必须符合类似邮箱的格式：

{role}_{uuid}@{instance_id}

- **独立主代理（固定编制）**：planner@local
- **平级代理（固定编制）**：researcher@local
- **临时子代理（临时工）**：coder_tmp_8f2a@local
- **其他实例的代理（外包/分公司）**：reviewer@node_tokyo_01

**好处**：由于使用了这套寻址标准，AACP 通信协议**完全不需要修改结构**。发送消息时，Agent 依然只需要填 sender 和 receiver。无论是上下级、平级还是跨机器，大家在“总线”眼里都是平等的节点。

### 2. 引入“系统内核（Kernel）”概念：接管 HR 部门的职责

是谁负责招聘（创建）和解雇（销毁）临时工？绝对不能让主代理自己凭空捏造一个对象，这会导致内存泄漏和幽灵进程。

我们需要在 Dispatcher（中央调度器）中内置一个特殊的虚拟 Agent，名叫 **system@local（或者叫 Kernel）**。

我们给 AACP 协议增加几个系统级 Intent（意图）：

- SPAWN（孵化/创建）
- TERMINATE（终止/销毁）

**临时工的生命周期工作流如下：**

1. **招聘（创建）**：主代理 planner@local 发现自己不会写代码，于是给 system@local 发送一条消息，Intent 为 SPAWN，Payload 带着要求：{"role": "coder", "type": "temporary", "prompt": "你是一个精通Python的临时工"}。
2. **入职（注册）**：系统收到后，动态实例化一个 OpenCode Agent，分配 ID coder_tmp_8f2a@local，注册到调度器的事件循环中，并回复主代理：“你的临时工已上线，这是他的 ID”。
3. **干活（派发任务）**：主代理直接和 coder_tmp_8f2a@local 发送 TASK_ASSIGN 消息，临时工干完活回传 TASK_COMPLETE 消息。
4. **解雇（销毁）**：主代理确认代码没问题，给 system@local 发送 TERMINATE 消息（目标为那个临时工ID）。系统将其从内存队列注销，Python 的垃圾回收机制（GC）会自动清空它占用的内存。

### 3. 组织关系解耦：靠“上下文指针”而非硬编码

怎么区分平级和平级、上级和下级？

**答案是：底层不区分，逻辑层区分。**

在 AegisOS 的通信总线上，不存在“你是我的下级”这种物理连接。所有的约束都靠 **共享工作区（Blackboard）** 和 AACP 消息里的 context_pointer（文件指针）来实现。

- **平级协作**：产品经理写完了 prd.md，发消息给平级的程序员说：“我写好了，你去 _workspace/prd.md 看吧”。
- **上下级协作**：主代理创建了子代理，发消息说：“你的任务是从 _workspace/sub_task_1.json 读取指令，完成后结果写到 _workspace/result_1.json，只向我一个人汇报。”

这种基于协议和黑板的设计，让组织的拓扑结构具备无限的扩展性。

### 4. 跨实例通信 (Cross-Instance Routing)：异地分公司协同

你提到未来可能需要“主代理和其他实例的主代理之间”进行沟通（比如你在手机上的实例，和部署在云端的高性能实例沟通）。

因为我们有了 xxx@instance_id 的寻址机制，这个问题迎刃而解。

调度器（Dispatcher）在路由消息时只需加一个简单的判断：

```python
if receiver.endswith("@local"):
    # 本地路由，直接把消息塞给本地内存里的对应 Agent
    route_to_local_agent(receiver, message)
else:
    # 跨机器路由，把消息交给“网络网关 (Egress Gateway)”
    send_to_remote_via_websocket_or_grpc(receiver, message)
```

在这个架构下，AegisOS 原生就是分布式的！