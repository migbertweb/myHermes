#!/bin/bash
# Launch a Hermes desktop client — start or refocus if already running
# Usage: ./launch.sh
#
# NOTE: This is the minimal version. For the full unified toggle/launch
# pattern, see the SKILL.md "Unified Launcher Script" section.

set -euo pipefail

APP_DIR="$HOME/hermes-chat"
MAIN_SCRIPT="$APP_DIR/main.py"
APP_TITLE="Viernes Chat"
PID_FILE="$HOME/.cache/viernes-chat.pid"
LOG_FILE="$HOME/.cache/viernes-chat.log"

# ── Dependency checks ──────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    notify-send "$APP_TITLE" "❌ Python3 no está instalado" -u critical
    exit 1
fi
if ! command -v hyprctl &>/dev/null; then
    notify-send "$APP_TITLE" "❌ hyprctl no encontrado" -u critical
    exit 1
fi

# ── Robust PID validation (check /proc/cmdline, not just kill -0) ──────────
is_our_pid() {
    local pid="$1"
    [ -z "$pid" ] && return 1
    kill -0 "$pid" 2>/dev/null || return 1
    [ -d "/proc/$pid" ] || return 1
    local cmdline
    cmdline=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || echo "")
    [[ "$cmdline" == *"main.py"* ]]
}

get_saved_pid() {
    [ -f "$PID_FILE" ] && cat "$PID_FILE" || echo ""
}

# ── Launch or refocus ─────────────────────────────────────────────────────
PID=$(get_saved_pid)
if is_our_pid "$PID"; then
    ADDRESS=$(hyprctl clients -j | jq -r --arg t "$APP_TITLE" \
        '.[] | select(.title == $t) | .address' | head -1)
    if [ -n "$ADDRESS" ]; then
        hyprctl dispatch focuswindow "address:$ADDRESS"
    fi
    exit 0
fi

# Not running — launch with nohup + log
cd "$APP_DIR"
nohup python3 "$MAIN_SCRIPT" >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
