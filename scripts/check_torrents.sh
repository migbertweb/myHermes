#!/bin/bash
# Check transmission torrents and report newly completed ones
# Stores completed torrent IDs in a temp file to avoid duplicate notifications

TR_STATE_FILE="/tmp/.hermes_torrents_completed"
TR_OUTPUT=$(transmission-remote -l 2>/dev/null)

# Skip header (line starting with "ID") and summary (line starting with "Sum:")
# Match lines where the second field is exactly "100%" or "Done"
COMPLETED=$(echo "$TR_OUTPUT" | awk '
/^ ID/ {next}
/^ Sum/ {next}
{
    if ($2 == "100%" || $2 == "Done") {
        # Get torrent name (rest of fields after ID)
        name = ""
        for(i = 2; i <= NF; i++) {
            if (i > 2) name = name " "
            name = name $i
        }
        # Remove leading "100% " or "Done " from name
        gsub(/^(100%|Done) /, "", name)
        print $1 ":" name
    }
}' 2>/dev/null)

if [ -z "$COMPLETED" ]; then
    echo "NO_NEW_COMPLETED"
    exit 0
fi

# Touch the state file if it doesn't exist
touch "$TR_STATE_FILE" 2>/dev/null

NOTIFIED=""
while IFS=: read -r tid tname; do
    if [ -n "$tid" ] && ! grep -qx "$tid" "$TR_STATE_FILE" 2>/dev/null; then
        echo "$tid" >> "$TR_STATE_FILE"
        NOTIFIED="${NOTIFIED}✅ Torrent #${tid} completado: ${tname}"$'\n'
    fi
done <<< "$COMPLETED"

if [ -n "$NOTIFIED" ]; then
    echo "COMPLETED:"
    echo "$NOTIFIED"
else
    echo "NO_NEW_COMPLETED"
fi
