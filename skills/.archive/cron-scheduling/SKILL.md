---
name: cron-scheduling
description: Schedule time-based tasks (reminders, recurring checks, one-shot jobs) with the cronjob tool. Covers timezone handling, schedule expressions, and user-specific conventions.
---

# Cron Scheduling

Use the `cronjob` tool to schedule reminders, recurring checks, daily briefings, and any task that should run without you present.

## When to use

- One-shot reminders ("remind me at 8 PM")
- Recurring checks ("check disk space every morning")
- Scheduled deliveries ("send the daily summary at 7 AM")
- NOT for: tasks that need interactive user input mid-run (cron runs unattended)

## Timezone: critical first step

**BEFORE scheduling any time-specific job, ALWAYS:**
1. Check the user's timezone from memory (`America/Sao_Paulo`, BRT UTC-3 for Migbert)
2. Check the **system timezone** (`date +%Z` or `timedatectl status`) — it may differ from the user's
3. If the system is not in the user's timezone, offer to change it with `sudo timedatectl set-timezone America/Sao_Paulo`
4. Verify the system clock is NTP-synchronized

### Why this matters
If the system is in UTC and you specify `2026-06-16T20:00:00` without an offset, the scheduler may interpret it in local (system) time — not the user's time. This causes the job to fire at the wrong hour.

## Schedule format: always use explicit offset

For **time-specific** schedules (not relative like "30m"), always use ISO 8601 **with timezone offset**:

```
# WRONG — ambiguous, depends on system timezone
schedule="2026-06-16T20:00:00"

# RIGHT — explicit BRT offset
schedule="2026-06-16T20:00:00-03:00"
```

For **recurring** schedules that should align to the user's local time, use a cron expression and ensure the system timezone matches the user's:

```
schedule="0 8 * * *"   # daily at 8 AM (system local time = user's time)
```

## User preferences

- **User**: Migbert (Brazil/São Paulo, UTC-3)
- **System timezone**: `America/Sao_Paulo`
- **Delivery**: always deliver to `origin` (current chat) unless asked otherwise. **Note: Specific platform targets (e.g., `deliver='telegram'`) are preferred when the user explicitly requests a specific mobile/external channel for status reports to avoid flooding the TUI session.**
- **Language**: Spanish — the prompt and delivery message should be in Spanish

## Prompt design for cron jobs

- Make prompts **self-contained** — the cron session has no memory of prior conversations
- Include the user's name and relevant context
- For reminders: state clearly WHAT to remind about and WHY
- For research prompts: include specific URLs, docs links, or search terms to investigate

## no_agent=True (watchdog/change-detection pattern)

For recurring tasks where the script output IS the message (no LLM reasoning needed), use `no_agent=True` with a `script`:

### When to use

- **Threshold watchdogs** — disk/memory/GPU usage alerts
- **Change detection** — poll an API or file, report diffs
- **Presence monitoring** — is a service alive?
- **CI/build status** — poll endpoint, emit on state change
- **Any task where the script produces exactly the message text the user should see**

### Delivery semantics (critical to get right)

| Stdout | Result |
|--------|--------|
| Non-empty | Delivered verbatim as the message to the user |
| Empty | **Silent** — nothing sent, user sees nothing |
| Non-zero exit / timeout | Error alert sent (watchdog can't fail silently) |

### Script design rules

1. **Silent on no-news**: produce empty stdout when there's nothing to report. Do NOT print "nothing new" or similar no-op text — that non-empty output gets delivered as a message every cycle.
2. **Use a state file**: track what's already been reported in `/tmp/.hermes_<purpose>_<id>` to avoid duplicate alerts across cycles.
3. **Git-friendly**: place scripts in `~/.hermes/scripts/`; `.sh`/`.bash` runs via bash, everything else via Python.
4. **Fail safely**: on error, either print an error message (user gets notified) or exit non-zero (system sends error alert).

### Example: torrent completion watchdog

```
# ~/.hermes/scripts/check_torrents.sh
STATE="/tmp/.hermes_torrents_completed"
OUTPUT=$(transmission-remote -l 2>/dev/null)
[ -z "$OUTPUT" ] && exit 0

COMPLETED=$(echo "$OUTPUT" | awk '/^ ID/{next} /^ Sum/{next} \
  {if($2=="100%"||$2=="Done"){print $1}}')
[ -z "$COMPLETED" ] && exit 0  # silent

touch "$STATE"
for id in $COMPLETED; do
  grep -qx "$id" "$STATE" && continue
  echo "$id" >> "$STATE"
  echo "✅ Torrent $id completed"
done
```

Cron job creation:

```
cronjob(
  action='create',
  name='Torrent checker',
  schedule='every 5m',
  script='check_torrents.sh',
  no_agent=True,
  deliver='origin'
)
```

See the `media/torrent-download` skill for a full working example.

## After creating a job

1. Verify the `next_run_at` field in the response shows the expected time with correct offset
2. Tell the user the local time it will fire: "te llega a las 8 PM BRT"
3. If the user corrects the timing, update the job with `cronjob(action='update', job_id=..., schedule=...)`

## Reference files

- `references/timezone-correction-example.md` — Full transcript of a timezone correction session (Honcho reminder, 2026-06-16). Shows the exact commands, user corrections, and resolution steps.

## Pitfalls

- **Don't assume** you know the user's timezone — check memory first
- **Don't use** bare UTC timestamps without offset for user-facing schedules
- **Don't forget** that `timedatectl set-timezone` requires `sudo`
- **Don't set** the cron schedule before verifying system timezone alignment
- If the system clock is unsynchronized (`timedatectl status` shows "NTP service: inactive"), enable NTP before scheduling
- After changing system timezone, existing cron jobs scheduled with bare timestamps may shift — update them with explicit offsets
