#!/bin/bash
ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new hetzner bash <<'REMOTE'
echo '📊 *Hetzner — Estado Actual*
━━━━━━━━━━━━━━━━━━━━━'

UP_SINCE=$(uptime -s | cut -d' ' -f1)
UP_RAW=$(uptime -p | sed 's/up //')
LOAD=$(cat /proc/loadavg | awk '{print $1, $2, $3}')
RAM=$(free -h | awk '/Mem:/{print $3 " usado de " $2 " — " $7 " libre"}')
DISK=$(df -h / | awk 'NR==2{print $3 " usado de " $2 " (" $5 ")"}')

echo ""
echo "⏱ *Uptime:* $UP_RAW"
echo "📆 Desde: $UP_SINCE"
echo ""
echo "💻 *CPU:* $LOAD (1/5/15 min)"
echo "🧠 *RAM:* $RAM"
echo "💾 *Disco:* $DISK"
echo ""
echo '🐳 *Contenedores:*'
docker ps --format '• {{.Names}} — {{.Status}}' 2>/dev/null | sed 's/ (healthy)//' | sed 's/ (unhealthy)/ ⚠️/' | head -20
REMOTE
