# 🧠 Agents As Systems

**From “agents as scripts” → “agents as systems”**

Most AI agent frameworks today are still just:

> prompt → tool → output
> 

Stateless. Disposable. Linear.

But that’s not how real systems work.

---

## ⚙️ What I’m actually building

I’m not trying to build another agent framework.

I’m building something closer to:

> **An operating system for agents**
> 

Where:

- agents behave like **processes**
- tasks become **workloads**
- coordination emerges from **protocols, not prompts**

This release is a small step toward that direction.

---

## 🚀 v0.1.4 — What changed (and why it matters)

### 1. Skills are now **pluggable capabilities**

Before:

- tools were tightly coupled to agent logic

Now:

- agents can dynamically acquire capabilities via a **Skill system**

### Introduced:

- `BaseSkill`
- dynamic skill registry inside `AACPAgent`

### First external skill:

- `WebScraperSkill` (powered by `httpx`)

**Why this matters:**

This is a shift from:

> “agent knows how to do things”
> 

to:

> “agent can *learn or attach* how to do things”
> 

This is closer to:

- Linux binaries
- plugin ecosystems
- capability injection

Not prompt engineering.

---

### 2. Agents are becoming **roles, not instances**

Added:

- `CoordinatorAgent`
- `WorkerAgent`

These are not just templates.

They define **coordination patterns**.

- Coordinator → decomposes tasks
- Worker → executes atomic work

**Why this matters:**

We’re moving toward:

> **multi-agent systems as default architecture**
> 

Instead of:

- one agent doing everything

---

### 3. First working **task execution loop**

Demo:

```bash
examples/fetch_and_report.py
```

This shows:

1. Coordinator receives a task
2. Spawns workers
3. Workers use skills (e.g. web scraping)
4. Results flow back
5. Final output is composed

This is the first time the system behaves like:

> a **closed-loop execution environment**
> 

Not just a chain.

---

### 4. SandboxRunner (early, but critical)

Implemented:

- restricted subprocess execution

This is foundational for:

- safe tool execution
- future “agent-created agents”
- long-running workloads

Think:

> `docker-lite` for agents (eventually)
> 

---

### 5. Dispatcher is getting **smarter**

Improved:

- `SPAWN` now auto-injects default LLMs

Meaning:

- less manual wiring
- more declarative agent creation

This is subtle, but important.

We’re moving toward:

> **agents defined by intent, not config**
> 

---

### 6. Reflexion loop is now **generalized**

Previously:

- only supported built-in actions

Now:

- supports both:
    - internal actions
    - external skills

This unlocks:

> **true self-execution loops**
> 

Where agents can:

- decide
- act
- evaluate
- iterate

---

## 🧭 The bigger direction

This release may look small.

But structurally, it’s a shift toward:

### → Agents as processes

### → Skills as capabilities

### → Tasks as schedulable workloads

### → Coordination via protocol (AACP)

---

## 🔥 What’s next

I’m heading toward:

- persistent agents (long-running)
- memory that isn’t just prompt stuffing
- agent-to-agent discovery (AACP layer — later)
- distributed execution

Ultimately:

> a **decentralized agent network**
> 
> 
> (like Bitcoin, but for intelligence)
> 

---

## 🧪 Try it

```bash
python examples/fetch_and_report.py
```

Watch agents:

- spawn
- collaborate
- complete a task loop

---

## 💬 I want your take

Most people are still building:

- better prompts
- better wrappers

I’m asking a different question:

> **What does an operating system for AI agents actually look like?**
> 

If you’re thinking about similar problems, I’d love to talk.