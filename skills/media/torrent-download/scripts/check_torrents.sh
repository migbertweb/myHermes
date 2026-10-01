#!/bin/bash
# check_torrents.sh — watchdog script for transmission completion notifications
# Used by a no_agent=True cron job (see SKILL.md "Automatic completion notifications")
#
# Behaviour:
#   - Parses `transmission-remote -l` output for 100%/Done torrents
#   - Compares against /tmp/.hermes_torrents_completed to avoid duplicate alerts
#   - Outputs completion messages ONLY on new completions (delivered verbatim)
#   - Silent (empty stdout) when nothing new — no spam every 5 minutes
#
# IMPORTANT: When deploying to ~/.hermes/scripts/ for a cron job, ensure
# the script stays SILENT on no-news (empty stdout = no delivery). Do NOT
# print "NO_NEW_COMPLETED" or any other no-op marker — that would trigger
# a notification every cycle.

TR_STATE_FILE="/tmp/.hermes_torrents_completed"
TR_OUTPUT=$(transmission-remote -l 2>/dev/null)

# Silent if command failed
[ -z "$TR_OUTPUT" ] && exit 0

# Skip header and summary, match 100% or Done lines
COMPLETED=$(echo "$TR_OUTPUT" | awk '
/^ ID/ {next}
/^ Sum/ {next}
{
    if ($2 == "100%" || $2 == "Done") {
        name = ""
        for(i = 2; i <= NF; i++) {
            if (i > 2) name = name " "
            name = name $i
        }
        gsub(/^(100%|Done) /, "", name)
        print $1 ":" name
    }
}' 2>/dev/null)

# Silent if nothing completed
[ -z "$COMPLETED" ] && exit 0

touch "$TR_STATE_FILE" 2>/dev/null

NOTIFIED=""
while IFS=: read -r tid tname; do
    if [ -n "$tid" ] && ! grep -qx "$tid" "$TR_STATE_FILE" 2>/dev/null; then
        echo "$tid" >> "$TR_STATE_FILE"
        NOTIFIED="${NOTIFIED}✅ Torrent #${tid} completado: ${tname}"$'\n'
    fi
done <<< "$COMPLETED"

# Print only if there is something new — otherwise silent
[ -n "$NOTIFIED" ] && echo "COMPLETED:" && echo "$NOTIFIED"
