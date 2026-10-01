---
name: kanban
description: >-
  Kanban workflow for Hermes Agent — orchestrator management, worker
  task execution, and Codex CLI lane integration. Absorbs the former
  kanban-orchestrator, kanban-worker, and kanban-codex-lane skills.
version: 1.0.0
author: Hermes Agent (merged from 3 absorbed skills)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, orchestrator, worker, codex, project-management, task-board]
    supersedes:
      - kanban-orchestrator
      - kanban-worker
      - kanban-codex-lane
---

# Kanban Workflow (Umbrella)

Consolidated Kanban workflow for Hermes Agent. Three layers:

1. **Orchestrator** — oversees the board, assigns tasks, manages workflow
2. **Worker** — picks up and executes individual tasks
3. **Codex Lane** — runs Codex CLI as a kanban worker on specific lanes

Archived narrow skills: kanban-orchestrator, kanban-worker, kanban-codex-lane.

---

## 1. Orchestrator

> **Legacy reference:** `references/kanban-orchestrator-original.md`

The orchestrator manages the Kanban board, tracks task state, and
coordinates between the PMB (project management board) system and
individual workers.

### Core Responsibilities

- Maintain board state via filesystem
- Detect ready items and assign to workers
- Handle worker completion callbacks
- Update board status (todo → in_progress → review → done)
- Manage WIP limits and lane configuration

### Board Format

```yaml
lanes:
  - name: backlog
  - name: todo
  - name: in_progress
    wip_limit: 3
  - name: review
  - name: done

cards:
  - id: "001"
    title: "Implement auth"
    lane: in_progress
    assignee: "worker-1"
    priority: high
```

### Orchestration Loop

```
1. Read board state
2. Check for ready items (dependencies met, lane has capacity)
3. Assign to available worker
4. Poll for completion
5. Move card to next lane
6. Repeat
```

---

## 2. Worker

> **Legacy reference:** `references/kanban-worker-original.md`

Workers pick up tasks from the orchestrator, execute them, and report back.

### Worker Contract

- Accept a task specification (goal, context, files)
- Execute the task
- Report result (success/failure, artifacts)
- Signal completion

### Task Execution Patterns

- Direct implementation (small tasks)
- Subagent delegation (complex tasks)
- Codex CLI delegation (coding tasks — see section 3)

---

## 3. Codex Lane

> **Legacy reference:** `references/kanban-codex-lane-original.md`

A specialized lane that uses Codex CLI for task execution via ACP transport.

### Setup

```bash
npm install -g @openai/codex
```

### Lane Configuration

In the kanban board, configure a "codex" lane:

```yaml
lanes:
  - name: codex_tasks
    runner: codex
    model: gpt-4o
```

### Worker Template

When the orchestrator assigns a Codex lane task:

```python
delegate_task(
    goal=task.goal,
    context=task.context,
    acp_command="codex",
    acp_args=["--acp", "--stdio"],
)
```
