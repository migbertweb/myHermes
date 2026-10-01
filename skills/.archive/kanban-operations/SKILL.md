---
name: kanban-operations
description: Use when a Hermes kanban task won't auto-start or is stuck.
---

# Kanban Operations (Hermes)

The operational model of the Hermes kanban system — how tasks actually move
from triage to done, who moves them, and how to diagnose a stuck board.
Complements (and supersedes the operational details of) the `kanban` skill,
which describes the legacy filesystem-YAML board model.

## Architecture — where the automation lives

- The **dispatcher is embedded in `hermes gateway`** (the messaging gateway),
  NOT in `hermes serve` (the JSON-RPC backend the desktop app connects to).
  `serve` hosts the dashboard/API; it does NOT dispatch kanban tasks.
- Gateway up → embedded dispatcher ticks every `kanban.dispatch_interval_seconds`
  (default 60). Each tick: auto-decompose triage tasks, promote `todo → ready`,
  then spawn workers for ready tasks.
- Gateway down → **tasks sit forever in triage/todo/ready**. No error, no log
  noise. This is the #1 cause of "my task won't start".

## Task state machine

```
triage ──auto-decompose / specify──▶ todo ──parents done──▶ ready ──dispatcher spawn──▶ running
   ▲                                                                                        │
   └────────────── block recurrence limit ───────────────────── blocked / back to triage ◀──┘
running ──worker done──▶ review ──judged──▶ done (or archived)
```

- `triage`: fresh tasks (dashboard-created or recurrence-blocked) awaiting
  decomposition. Auto-decomposer fans them out (LLM, `kanban_decomposer`
  provider) or specifies them as single tasks; capped per tick by
  `kanban.auto_decompose_per_tick` (default 3).
- `todo → ready`: only when all parents are done (parent-gating).
- `ready`: has an assignee and no open parents → dispatcher claims and spawns
  the worker as a subprocess (worktree workspace).

## CLI surface

```bash
hermes kanban create <title> [--body "<spec>"] [--priority N] [--triage]
hermes kanban list                       # also: ls — NO --board flag (see pitfall)
hermes kanban show <task_id>
hermes kanban assign <task_id> --user <profile>
hermes kanban promote <task_id>          # move up a state
hermes kanban claim <task_id>
hermes kanban complete <task_id>
hermes kanban dispatch --dry-run --json  # preview one tick without spawning
hermes kanban diagnostics                # board health
hermes kanban boards list
hermes kanban runs / log / tail          # worker run history
hermes kanban daemon                     # DEPRECATED legacy standalone dispatcher
```

**There is NO `hermes kanban move` subcommand.** Use `promote`/`claim`/
`complete` or the gateway dispatcher.

### Creating tasks (`hermes kanban create`)

- `--priority` is an **int tiebreaker** (e.g. `--priority 50`), NOT a string —
  `--priority high` fails with `invalid int value: 'high'`.
- `--body` is the full task spec / opening post; pass a file's content with
  `--body "$(cat <file>)"` so the worker gets the whole spec inline (survives
  newlines, code blocks, emoji).
- Default (no flags) lands the card in `ready` right away (no parents → promoted
  at once), so the dispatcher spawns a worker on the next tick that tries the
  WHOLE card in one run. For a large multi-part spec, prefer `--triage`: the
  auto-decomposer (`kanban.auto_decompose`) splits it into subtasks instead.
  `--goal` runs a judge loop for open-ended cards.
- `--created-by <name>` records authorship (default: `user`).
- New cards show `(unassigned)` even in `ready` — the dispatcher assigns
  `kanban.default_assignee` at spawn time. Not a stuck task; verify the config
  key exists and points at a real profile (`hermes profile list`).

## Diagnostic path (stuck task)

1. `hermes gateway status` → if "Gateway is not running", that's the root cause.
   Fix: `hermes gateway start` (background service) or `hermes gateway run`
   (foreground). Next tick (≤60s) picks up the task.
2. `hermes kanban dispatch --dry-run --json` → shows what a tick *would* do
   without spawning (fields: spawned, promoted, reclaimed, skipped_*).
3. Check the gateway is actually dispatching:
   `grep "kanban dispatcher: embedded in gateway" ~/.hermes/logs/gateway.log`.
   Note: gateway.log can be stale after upgrades; the desktop backend logs to
   `~/.hermes/logs/agent.log` / `gui.log` instead.
4. `hermes kanban show <task_id>` → status, assignee, workspace, event history
   (events show who assigned/promoted and when).

## Config keys that govern dispatch (`~/.hermes/config.yaml`)

```yaml
kanban:
  dispatch_in_gateway: true        # dispatcher embedded in gateway (default)
  dispatch_interval_seconds: 60
  failure_limit: 2                 # auto-block after N consecutive spawn failures
  orchestrator_profile: devops-chief
  default_assignee: devops-chief
  auto_decompose: true             # triage → workgraph automatically
  auto_decompose_per_tick: 3
kanban_decomposer:                 # aux LLM for decomposition
  provider: auto

## Retry budgets — two INDEPENDENT limits

| Failure kind | Controlled by | Default | Notes |
|---|---|---|---|
| General (timeout, crash, spawn failure) | `kanban.failure_limit` (config) | 2 | unified `consecutive_failures` counter |
| Protocol violation (rc=0, no kanban call) | `_PROTOCOL_VIOLATION_FAILURE_LIMIT` (const in `hermes_cli/kanban_db.py` ~7553) | 3 | violation-only streak; below-budget violations DON'T consume the unified counter |
| Per-task override (both) | `max_retries` DB column | NULL → fall through | set via `hermes kanban create --max-retries N` (>= 1; 1 = trip on first failure); top precedence over both budgets |

- `kanban.failure_limit` only widens the GENERAL circuit breaker. Protocol
  violations use their own streak budget (constant 3, or per-task `max_retries`).
- The dispatcher reads kanban config when its loop starts → after editing
  config.yaml, restart the gateway (`hermes gateway restart` /
  `systemctl --user restart hermes-gateway`) for changes to take effect.
- The Electron desktop app has NO kanban logic — it is surface only. All knobs
  live in config.yaml + gateway + board DB.
- Retry worker gets the prior attempt's error as guidance: "If the prior run
  already did the work, verify it and report the result via kanban_complete; a
  run that ends without a terminal kanban call counts as failed no matter what
  it did." (Code comment: ~96% of violations complete on a later run.)
```

## Worker protocol — mandatory calls

Every worker **must** exit by calling one of:
- `hermes kanban complete <task_id>` — task succeeded
- `hermes kanban block <task_id> --reason "..."` — task blocked (needs user input)

**Worker exits with `rc=0` but NO kanban call → dispatcher marks `protocol_violation` → re-runs until the VIOLATION retry budget is exhausted → task blocks.**

This is the #2 cause of "task won't complete" after gateway not running.

⚠ The violation budget is INDEPENDENT of `kanban.failure_limit`. Raising
`kanban.failure_limit` in config.yaml does NOT give protocol violations more
retries — see "Retry budgets" below.

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
# echo "Creating EnRaya.jsx..."
# echo "Creating Snake.jsx..."

# Mandatory: report result
hermes kanban complete "$TASK_ID"
# OR on failure:
# hermes kanban block "$TASK_ID" --reason "Missing dependency foo"
```

**Reference:** `references/worker-template.sh` — boilerplate worker script with error handling.


## DB internals (bypass, not the flow)

- Per-board SQLite DB: `~/.hermes/kanban/boards/<board>/kanban.db`
  (tables: `tasks`, `task_events`, `task_comments`, `task_runs`, ...).
- `~/.hermes/kanban/current` holds the active board slug.
- Direct `UPDATE tasks SET status='todo' WHERE id=...` works but bypasses
  events, ready-promotion and parent gating — prefer the CLI verbs or just
  start the gateway. Only use SQL for read-only inspection.

## Pitfalls

- **Perfil gateway sin sección `auxiliary` → decompose de triage muere con 402.**
  Síntoma (journal del gateway que hostea el dispatcher, cada intento de
  decompose): `Auxiliary: marking auto unhealthy for 600s (payment / credit
  error)` + `PAID lane engaged ... OpenRouter fallback model '...' is not a
  :free SKU`. La tarea se queda EN TRIAGE para siempre, sin "tick failed".
  Causa: `auxiliary.kanban_decomposer` no existe en el config.yaml DEL PERFIL
  (los perfiles con config propio NO heredan la sección del config global);
  el lane "auto" resuelve al provider principal del perfil (p.ej. OmniRoute
  custom) → 402 → fallback OpenRouter. Fix: añadir a
  `~/.hermes/profiles/<p>/config.yaml`:
  ```yaml
  auxiliary:
    kanban_decomposer:
      provider: deepseek
      model: ''
      base_url: ''
      api_key: ''
      timeout: 180
  ```
  (usar ruamel.yaml, no patch(), para preservar formato) y reiniciar el
  gateway. Verificado 2026-08-08: con esto el decompose pasó triage→todo y
  spawnó workers en el siguiente tick. Diagnóstico rápido:
  `python3 -c "import yaml;print('aux' in yaml.safe_load(open('<cfg>')))"`.
- **El lock del dispatcher lo toma CUALQUIER gateway por carrera de arranque.**
  Todos los `hermes-gateway-*.service` compiten por
  `~/.hermes/kanban/.dispatcher.lock` al arrancar; el primero gana, sin
  importar `orchestrator_profile`. Si el que gana es un perfil cuyo config
  no tiene `auxiliary.kanban_decomposer` (o cuyo provider principal devuelve
  402), todo el dispatch queda bloqueado silenciosamente. Verificar quién
  tiene el lock: `lslocks | grep dispatcher`. Fix si ganó el perfil
  equivocado: `systemctl --user stop hermes-gateway-<wrong>.service` y
  `systemctl --user restart hermes-gateway-<orchestrator>.service` (el
  correcto toma el lock al arrancar; los demás no reintentan en caliente).
- **Board dir with an uninitialized `kanban.db` (0 tables) breaks the tick forever.**

  Symptom in journalctl/gateway log every 60s:
  `sqlite3.OperationalError: no such table: tasks` at `release_stale_claims`
  (`kanban_db.py`), `tick failed on board <slug>`. The corrupt-board quarantine
  (`disabled_corrupt_boards` in `kanban_watchers.py`) only catches "not a valid
  SQLite database" — a valid-but-schemaless file falls through and fails on
  EVERY tick. Root cause: creating/`boards delete` from the desktop UI (or an
  interrupted create) leaves `kanban.db` with 0 tables. Tasks on that board can
  never dispatch or transition (looks like "task stuck / Block without saying
  if it finished"). Fix: `rm -rf ~/.hermes/kanban/boards/<slug>` (or recreate
  via `hermes kanban init` on the active board), then the next tick is clean.
  Verify with:
  `journalctl --user -u hermes-gateway-<profile> --since "10 minutes ago" -o short-iso | grep "tick failed"`
  Dispatcher errors land in the HOSTING profile gateway's journal (each profile
  gateway is its own systemd unit), NOT `~/.hermes/logs/gateway.log`. Confirm a
  schemaless board: `SELECT count(*) FROM sqlite_master WHERE type='table'`
  → 0 (healthy boards have 8 tables). Error site: `release_stale_claims`
  `kanban_db.py:4487`. Full map: `references/dispatcher-internals.md`.
- `hermes kanban` subcommands read the *current* board; `--board <slug>` is
  NOT accepted by every subcommand (`list` rejects it with "unrecognized
  arguments: --board"). Pin with the `HERMES_KANBAN_BOARD` env var or switch
  with `hermes kanban boards switch <slug>`, then run plain `list`.
- Assignee must be a real profile name (`hermes profile list`); an unknown
  assignee → task skips spawn (`skipped_unassigned` / `skipped_nonspawnable`
  in the dispatch dry-run).
- The legacy standalone `hermes kanban daemon` is deprecated; the canonical
  dispatcher is the gateway. `daemon --force` only when dispatch_in_gateway
  is off.
- Manual SQL edits to a task the dispatcher is managing can race with WAL
  frames — read-only inspection is safe, writes are not.

## References

- `references/dispatcher-internals.md` — code-level internals: file paths in
  the hermes-agent repo (`gateway/kanban_watchers.py`, `hermes_cli/kanban_db.py`),
  function names, DB schema probes, gotchas hit while debugging a stuck task.
  Includes the 2026-08-08 retry-budgets / protocol_violation deep-dive (exact
  line numbers, breaker-trip flow, fix levers).

## Verification

- `hermes gateway status` shows the service running.
- `hermes kanban dispatch --dry-run --json` reports spawned/promoted ≥ 1 for a
  ready task.
- `hermes kanban show <id>` shows status advanced triage → todo → ready →
  running, with events documenting each transition.

---

## Gateway setup checklist

**Problem:** `hermes gateway` not running → dispatcher inactive → tasks stuck in `triage`.

**Fix:** Install and start gateway for all profiles:

```bash
# Check current status
hermes gateway list

# Install and start for each profile
for profile in default coder-back coder-front devops-chief reseach; do
  hermes gateway install --profile "$profile"
done

# Verify all are active
hermes gateway list
systemctl --user status hermes-gateway-devops-chief
```

After install, systemd creates user services:
- `hermes-gateway.service` (default)
- `hermes-gateway-coder-back.service`
- `hermes-gateway-coder-front.service`
- `hermes-gateway-devops-chief.service`
- `hermes-gateway-reseach.service`

**Logs:** `journalctl --user -u hermes-gateway-devops-chief -f`

The desktop backend (`hermes serve`) does NOT host the dispatcher — only `hermes gateway` does.
