# Timezone Correction Example — Honcho Reminder (2026-06-16)

## Context
User asked for a reminder at "8 PM" to research Honcho (memory system for AI agents).

## What went wrong (first attempt)
1. **Assumed** user was in Venezuela (UTC-4) based on earlier TTS voice preference (es-MX)
2. **Scheduled** the job at midnight UTC (= 8 PM Venezuela time)
3. **Did not verify** system timezone before scheduling

## User corrections
1. "Opa no estoy en Venezuela.. estoy en Brasil y uso el Horario de Sao Paulo" → User is in Brazil (UTC-3)
2. "😲 esa no es la hora... La hora es 17:24" → Server was in UTC, showing a different time than user expected
3. "Huso horario América/São Paulo" → Explicit instruction to set system timezone

## Corrected approach
1. Saved user's timezone to memory: `America/Sao_Paulo (BRT, UTC-3)`
2. Changed system timezone: `sudo timedatectl set-timezone America/Sao_Paulo`
3. Updated cron schedule with explicit offset: `2026-06-16T20:00:00-03:00`

## Commands used
```bash
# Check current time and timezone
date '+%Y-%m-%d %H:%M:%S %Z %z'
timedatectl status

# Change timezone (requires sudo)
sudo timedatectl set-timezone America/Sao_Paulo

# Verify NTP sync
timedatectl show --property=Timezone --value
```

## Key lesson
**Always** verify the user's timezone from memory AND the system timezone BEFORE scheduling any time-specific task. Use ISO 8601 with explicit offset for one-shot schedules.
