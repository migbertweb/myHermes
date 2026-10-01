# Session findings — dispatcher internals (2026-08-02)

Debug transcript from "task stuck in triage" on laptop CachyOS (profile `default`,
board `workapp`, workers coder-back/coder-front/devops-chief/reseach).

## Root cause confirmed

`hermes gateway` (messaging) was NOT running. Only `hermes serve` (desktop
backend, PID under `hermes desktop`) was up. `serve` does not host the
dispatcher → task sat in `triage` for ~24 min with zero automation.

Config was already correct (`dispatch_in_gateway: true`, `auto_decompose: true`,
`orchestrator_profile: devops-chief`). Config was NOT the problem — service
lifecycle was.

## Code locations (hermes-agent repo)

- `gateway/kanban_watchers.py` — the embedded dispatcher loop.
  - Log line to grep: `kanban dispatcher: embedded in gateway (interval=%.1fs)`
  - `_auto_decompose_tick()` (line ~1343): fans out triage tasks, gated by
    `kanban.auto_decompose_per_tick` (default 3), flag re-read from config
    EVERY tick (#49638) so `auto_decompose: false` stops fan-out on next tick.
  - Per-tick order: reap zombies → auto-decompose → `_tick_once` (per-board:
    reclaim stale → detect stale/crashed → promote todo→ready → spawn ready).
- `hermes_cli/kanban_db.py` — state machine core.
  - `VALID_STATUSES = {triage, todo, scheduled, ready, running, blocked, review, done, archived}`
  - `specify_triage_task()` (~5967): triage → todo in one txn; then
    `recompute_ready()` flips parent-free todos straight to `ready`.
  - `decompose_triage_task()` (~6058): fans root into children, promotes root
    to todo; root promotes to ready when all children done.
  - `dispatch_once()` (~8204) / `_dispatch_once_locked()` (~8274): single-writer
    dispatch lock per board DB path; `max_spawn` is a live concurrency cap
    (counts running + this tick's spawns).
  - `release_stale_claims` / `detect_stale_running` / `detect_crashed_workers`
    — the reclaim trio; stale claim crash was seen 2026-07-12 in gateway.log.
- `hermes_cli/kanban.py` line ~200 — the "No gateway is running" guidance
  string that `hermes kanban show`/diagnostics emit.
- `docs/kanban/multi-gateway.md` — single-dispatcher posture: only one gateway
  owns dispatch; others set `kanban.dispatch_in_gateway: false`.

## DB schema (read-only probes)

```sql
-- ~/.hermes/kanban/boards/<board>/kanban.db
SELECT name FROM sqlite_master WHERE type='table';
-- tasks, task_links, task_comments, task_events, task_runs,
-- task_attachments, kanban_notify_subs, sqlite_sequence
SELECT * FROM tasks;  -- columns: id, title, body, assignee, status, ...
```

Bypass used once: `UPDATE tasks SET status='todo' WHERE id='t_03e1c32e'`
(moved the task manually). Works, but skips events + ready-promotion; the
correct flow is gateway dispatch. Documented in SKILL.md as "bypass, not flow".

## Gotchas hit

- `hermes kanban move` does not exist → argparse error listing valid actions
  (assign, promote, claim, complete, ...). Use `promote`.
- `~/.hermes/profiles/<p>/kanban/` does not exist — boards are global under
  `~/.hermes/kanban/boards/`; `--profile` on `hermes kanban` just selects the
  profile context, not a per-profile board store.
- `~/.hermes/logs/gateway.log` frozen at 2026-07-12; live desktop backend logs
  in `agent.log` / `gui.log`. Always check file mtime before trusting a log.
- `hermes kanban daemon` is deprecated (`--force` flag escapes the deprecation
  guard); gateway is canonical.

---

# Retry budgets / protocol_violation deep-dive (2026-08-08)

Investigated for "task goes to Block without saying whether it finished" —
symptom: worker did the work, exited rc=0, but the card still went `blocked`.

## Root cause

`protocol_violation`: worker subprocess exited cleanly WITHOUT calling
`kanban_complete` / `kanban_block`. The dispatcher can't tell if the work
finished → retries with a bounded budget → blocks with `gave_up` event.
User-facing symptom on the board: task stuck in Block, no completion info.

## Code locations (hermes-agent repo, verified 2026-08-08)

- `hermes_cli/kanban_db.py:7553` — `_PROTOCOL_VIOLATION_FAILURE_LIMIT = 3`
  (constant, NOT configurable via config.yaml).
- `hermes_cli/kanban_db.py:7562` `_protocol_violation_streak()` — walks the
  task's closed runs newest-first (scan limit 50); `rate_limited` runs are
  neutral, any other outcome breaks the streak.
- `hermes_cli/kanban_db.py:7612` `detect_crashed_workers()` — reclaims `running`
  tasks whose PID is dead. `clean_exit` + still-running → stamps
  `protocol_violation` marker + event, drops task back to `ready`.
- `hermes_cli/kanban_db.py:7811-7857` — breaker trip: `streak >= violation_limit`
  → `_record_task_failure(force_trip=True)` → `blocked` + `gave_up` event.
  `violation_limit` = per-task `max_retries` if set, else the constant 3.
  Below-budget violations do NOT tick the unified `consecutive_failures`
  counter (the two budgets stay independent).
- `gateway/kanban_watchers.py:1084-1100` — `kanban.failure_limit` read from
  config (default `DEFAULT_FAILURE_LIMIT = 2`, kanban_db.py:6742). Read at
  dispatcher loop start → gateway restart required for config changes.
- `hermes_cli/kanban.py:1490-1516` — `hermes kanban create --max-retries N`
  writes the per-task override column (must be >= 1; 1 = trip on first failure).
  `hermes kanban show <id>` prints `max-retries: N (task)` when set.

## Exact error text surfaced to the user/board

"worker exited cleanly (rc=0) without calling kanban_complete or kanban_block —
protocol violation. If the prior run already did the work, verify it and report
the result via kanban_complete; a run that ends without a terminal kanban call
counts as failed no matter what it did."

## Fix levers (in order)

1. Structural: worker must always end with `hermes kanban complete <id>` /
   `kanban block <id> --reason "..."` (see templates/worker.sh).
2. Per-task margin: `hermes kanban create ... --max-retries 5` (top precedence
   over BOTH budgets).
3. Global general-failure margin: `kanban.failure_limit: 5` in config.yaml +
   gateway restart (does NOT affect protocol violations).
4. Editing the constant in the repo is NOT durable — lost on `hermes update`.

## Orphan board DB — "no such table: tasks" kills every tick (2026-08-08)

Symptom (per-gateway journal, NOT gateway.log):

```
ERROR gateway.run: kanban dispatcher: tick failed on board <slug>
  File "hermes_cli/kanban_db.py", line 4487, in release_stale_claims
sqlite3.OperationalError: no such table: tasks
```

Root cause: board dir exists but its `kanban.db` has ZERO tables (schema never
initialized). Seen when boards are "deleted" from the Hermes Desktop dashboard —
the dir/DB file is left behind — or when board creation is abandoned mid-setup.
The dispatcher iterates every board dir under `~/.hermes/kanban/boards/`; the
corrupt-board quarantine (`_is_corrupt_board_db_error` in kanban_watchers.py)
only matches "file is not a valid SQLite database", NOT "no such table" → the
tick fails every `dispatch_interval_seconds` forever, and no task on that board
can dispatch or transition. On this box, gateway `coder-front` was dispatching
boards slug/workapp/miappcentral (each profile gateway is a separate unit).

Diagnosis:
- `journalctl --user -u hermes-gateway-<profile> | grep "tick failed"`
- `sqlite3 ~/.hermes/kanban/boards/<slug>/kanban.db "SELECT count(*) FROM
  sqlite_master WHERE type='table'"` → 0 (healthy = 8 tables)

Fix: `rm -rf ~/.hermes/kanban/boards/<slug>` for boards no longer wanted;
re-create via `hermes kanban boards create` so the schema initializes. Confirm
the tick stops erroring within one interval.

## Worker spawn internals — what protocol_violation is NOT (2026-08-08)

Verified in `_default_spawn()` (kanban_db.py:9067-9267) while chasing
"worker exits rc=0 without reporting":

- The worker IS a CLI subprocess:
  `hermes -p <profile> --cli --accept-hooks chat -q "work kanban task <id>"`
  (env: HERMES_KANBAN_TASK, HERMES_KANBAN_BOARD/DB/WORKSPACE, HERMES_PROFILE,
  TERMINAL_CWD pinned to workspace, HERMES_SESSION_SOURCE=kanban).
- Reporting is via the AGENT TOOLS `kanban_complete` / `kanban_block`, appended
  by model_tools whenever `HERMES_KANBAN_TASK` is set — NEVER by shelling out to
  the `hermes` binary. "Worker has no CLI access" is NOT a real failure mode;
  toolsets restrictions don't strip these tools.
- goal_mode workers REQUIRE the fully-quiet `-Q` flag; without it the worker
  takes one turn, prints text, exits 0 → protocol_violation (incident
  2026-06-09 t_d9cbe312; fixed upstream, `cmd.append("-Q")`).
- `--cli` is forced and `HERMES_TUI` popped so a profile with
  `display.interface: tui` can't TUI-bail-out (exit 0 without doing the task →
  protocol_violation on every attempt).
- Therefore a protocol_violation almost always means: the worker model ended its
  turn without emitting the terminal tool call. Retry injects the prior-attempt
  error as corrective guidance (~96% complete on a later run, per code comment).
