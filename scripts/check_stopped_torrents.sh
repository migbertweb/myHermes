#!/bin/bash
# Check stopped torrents and restart those with metadata/peers
# Used by: cron job "check-stopped-torrents"

STOPPED_IDS=(12 13 19 20 22 23 26 27)
RESTARTED=()
STILL_DEAD=()

for id in "${STOPPED_IDS[@]}"; do
  # Get torrent details
  NAME=$(transmission-remote -t "$id" -i 2>/dev/null | grep "Name:" | sed 's/.*Name: //')
  STATUS=$(transmission-remote -t "$id" -i 2>/dev/null | grep "State:" | sed 's/.*State: //')
  PEERS=$(transmission-remote -t "$id" -i 2>/dev/null | grep "Peers:" | head -1)
  PIECE=$(transmission-remote -t "$id" -i 2>/dev/null | grep "Piece Size:" | sed 's/.*Piece Size: //')

  # Check if it has metadata or peers
  HAS_METADATA=false
  HAS_PEERS=false

  if [ "$PIECE" != "None" ] && [ -n "$PIECE" ]; then
    HAS_METADATA=true
  fi

  if echo "$PEERS" | grep -q "connected to [1-9]"; then
    HAS_PEERS=true
  fi

  if [ "$HAS_METADATA" = true ] || [ "$HAS_PEERS" = true ]; then
    transmission-remote -t "$id" --start 2>&1 > /dev/null
    RESTARTED+=("$id ($NAME)")
  else
    STILL_DEAD+=("$id ($NAME)")
  fi
done

echo "=== Verificación de torrents stopped ==="
echo "Fecha: $(date '+%Y-%m-%d %H:%M')"
echo ""
echo "✅ Restarteados (tienen metadata o peers):"
if [ ${#RESTARTED[@]} -eq 0 ]; then
  echo "  Ninguno — todos siguen sin metadata"
else
  for t in "${RESTARTED[@]}"; do
    echo "  - $t"
  done
fi
echo ""
echo "❌ Siguen stopped (sin metadata ni peers):"
for t in "${STILL_DEAD[@]}"; do
  echo "  - $t"
done
