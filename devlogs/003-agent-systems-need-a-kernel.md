## The Problem We Kept Running Into

While building and running LLM-based agents, we kept seeing the same class of failures:

- Infinite reasoning loops
- Repeated tool calls with no progress
- Tasks getting stuck in retry cycles
- Corrupted or inconsistent task state
- Zombie agents that never terminate

At first glance, these look like implementation bugs.

They are not.

They are symptoms of a deeper issue:
**we were letting the LLM manage system state.**

---

## What We Tried (and Why It Didn't Work)

Like most teams, we initially tried to patch these issues at the prompt level:

- Adding stricter instructions ("do not repeat", "terminate when done")
- Limiting steps heuristically
- Wrapping tools with retry / backoff logic
- Introducing skill abstractions to structure behavior

These helped — temporarily.

But none of them solved the core problem.

Because the system still relied on the LLM to:

- decide when a task is done
- manage state transitions
- coordinate execution flow

And LLMs are not designed for deterministic state management.

---

## The Core Insight

The breakthrough came when we reframed the problem:

> **State consistency is not an intelligence problem.  
> It is a systems problem.**

LLMs are good at:
- reasoning
- planning
- generating actions

But they are fundamentally unreliable at:
- enforcing invariants
- managing shared state
- guaranteeing termination

---

## What We Changed

Instead of trying to “fix” the agent with better prompts,  
we moved critical responsibilities out of the LLM entirely.

We introduced a deterministic control layer inside the Coordinator.

### 1. Single Writer Principle

Only the Coordinator is allowed to modify `plan.json`.

Workers can no longer mutate shared state directly.  
They can only submit proposals.

---

### 2. Explicit Task State Machine

Every task must follow:
