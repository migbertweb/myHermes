# Worker Script Template for Hermes Kanban

## Problem

Worker exits with `rc=0` but **no `kanban_complete` or `kanban_block` call** → dispatcher marks `protocol_violation` → re-runs until `failure_limit` → task blocks.

## Solution

Create a wrapper script that:

1. Runs your task logic
2. Always exits via `hermes kanban complete` (success) or `hermes kanban block` (failure)

## Template

```bash
#!/bin/bash
TASK_ID="$1"
WORKSPACE="$2"

cd "$WORKSPACE" || exit 1

# ... run your logic ...

hermes kanban complete "$TASK_ID"
```

## In `SKILL.md`

Add this section:

```markdown
## Worker protocol — mandatory calls

Every worker **must** exit by calling one of:
- `hermes kanban complete <task_id>` — task succeeded
- `hermes kanban block <task_id> --reason "..."` — task blocked

**Symptom in `hermes kanban log <id>`:**
```
worker exited cleanly (rc=0) without calling kanban_complete or kanban_block
```

**Fix pattern** (create `worker.sh` in project repo):
```bash
#!/bin/bash
TASK_ID="$1"
WORKSPACE="$2"
cd "$WORKSPACE" || exit 1
# ... run your logic ...
hermes kanban complete "$TASK_ID"
```

**Reference:** `templates/worker.sh` — boilerplate worker script.
```
