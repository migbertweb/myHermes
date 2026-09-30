#!/usr/bin/env python3
"""
Agenda notification checker — runs every 2 min via cron.
Outputs a Telegram message if there are tasks to notify 15 min before.
"""
import subprocess
import json
import sys
from datetime import datetime

SCRIPT = "/home/piro/.hermes/agenda/agenda.py"

result = subprocess.run(
    [SCRIPT, "notify"],
    capture_output=True, text=True, cwd="/home/piro/.hermes/agenda"
)

if not result.stdout.strip():
    # No notifications to send — silent exit
    sys.exit(0)

try:
    data = json.loads(result.stdout)
except json.JSONDecodeError:
    sys.exit(0)

if data.get("count", 0) == 0:
    sys.exit(0)

now = datetime.now().strftime("%H:%M")
lines = [f"⏰ *Agenda — {now}*", ""]
for t in data["notify"]:
    prio = "🔴 " if t["priority"] >= 2 else "🟡 " if t["priority"] >= 1 else ""
    lines.append(f"  {prio}#{t['id']} *{t['title']}* — às {t['time']}")

lines.append("")
lines.append("Responde con `agenda hoy` para ver todo el día.")
print("\n".join(lines))
