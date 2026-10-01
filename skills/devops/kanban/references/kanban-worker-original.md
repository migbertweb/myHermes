# kanban-worker (original content — absorbed into `kanban` umbrella)

The worker skill defined the worker contract: accept task specification (goal, context, files), execute the task, report result (success/failure, artifacts), signal completion. Covered direct implementation, subagent delegation, and Codex CLI delegation patterns. Absorbed into the `kanban` umbrella skill's Worker section.

## Key preserved patterns

- Worker contract: accept → execute → report → signal
- Direct implementation for small tasks
- Subagent delegation for complex tasks
