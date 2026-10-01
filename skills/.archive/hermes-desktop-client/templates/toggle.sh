#!/bin/bash
# Unified toggle/launch/hide for a Hermes desktop client on Hyprland.
# Uses SIGUSR1 IPC for toggle — Python handles show/hide internally.
# Single script — bind this directly to a key.
#
# Usage:   toggle.sh          # toggle show/hide (SIGUSR1 to existing process)
#          toggle.sh launch   # force launch
#          toggle.sh hide     # force hide (SIGUSR1 if process exists)
#
# Customization: change PROJECT_DIR, MAIN_SCRIPT, PID_FILE, LOG_FILE at top.
#
# Bind in Hyprland:
#   bind = SUPER, SPACE, exec, ~/hermes-chat/toggle.sh
#
# Or install to /usr/local/bin/ and bind without path:
#   sudo cp toggle.sh /usr/local/bin/viernes-chat
#   sudo chmod +x /usr/local/bin/viernes-chat
#   bind = SUPER, SPACE, exec, viernes-chat
#
# Key features:
# - SIGUSR1 IPC: Python manages show/hide internally (no hyprctl race conditions)
# - Lock file prevents concurrent runs from rapid keybinding
# - PID validation via /proc/$PID/cmdline (not just kill -0)
# - Orphan detection: finds main.py processes that lost their PID file
# - Does NOT need jq — no hyprctl calls for toggle

PROJECT_DIR="$HOME/hermes-chat"
MAIN_SCRIPT="$PROJECT_DIR/main.py"
PID_FILE="$HOME/.cache/app.pid"
LOCK_FILE="$HOME/.cache/app.lock"
LOG_FILE="$HOME/.cache/app.log"

# ── 1. Dependency checks ──────────────────────────────────────────────────

for cmd in python3 hyprctl; do
    if ! command -v "$cmd" &>/dev/null; then
        notify-send "$(basename "$0")" "Falta $cmd" -u critical
        exit 1
    fi
done

if ! python3 -c "import PyQt6" 2>/dev/null; then
    notify-send "$(basename "$0")" "PyQt6 no instalado - pip install PyQt6" -u critical
    exit 1
fi

if [ ! -f "$MAIN_SCRIPT" ]; then
    notify-send "$(basename "$0")" "No se encuentra $MAIN_SCRIPT" -u critical
    exit 1
fi

# ── 2. Lock (atomic mkdir — prevents concurrent launches) ─────────────────

cleanup_lock() { rm -rf "$LOCK_FILE"; }
trap cleanup_lock EXIT

if ! mkdir "$LOCK_FILE" 2>/dev/null; then
    # Another instance is already running the toggle
    exit 0
fi

# ── 3. Helpers ───────────────────────────────────────────────────────────

get_saved_pid() {
    cat "$PID_FILE" 2>/dev/null || echo ""
}

# Validates both that the PID exists AND that it's actually our Python app
is_running() {
    local pid="$1"
    [ -z "$pid" ] && return 1
    kill -0 "$pid" 2>/dev/null || return 1
    # Confirm this PID belongs to our app via /proc/PID/cmdline
    [ -r "/proc/$pid/cmdline" ] && grep -q 'main\.py' "/proc/$pid/cmdline" 2>/dev/null
}

# Finds orphan main.py processes (running but without a valid PID file)
find_orphan() {
    local pids
    pids=$(pgrep -f 'python3.*/.*main\.py' 2>/dev/null | grep -v -e '^$$\|grep' || true)
    for pid in $pids; do
        if [ -r "/proc/$pid/cmdline" ] && grep -q 'main\.py' "/proc/$pid/cmdline" 2>/dev/null; then
            echo "$pid"
            return 0
        fi
    done
    return 1
}

# Bring window to front (only used on launch, not toggle)
bring_to_front() {
    hyprctl dispatch movetoworkspace "+1,address:$1" 2>/dev/null
    hyprctl dispatch focuswindow "address:$1" 2>/dev/null
}

find_window() {
    hyprctl clients -j 2>/dev/null | jq -r \
      'map(select(.title == "Viernes Chat" or .title == "hermes-chat")) | first | .address // ""'
}

# ── 4. Launch ─────────────────────────────────────────────────────────────

do_launch() {
    cd "$PROJECT_DIR" 2>/dev/null || {
        notify-send "$(basename "$0")" "No se puede acceder a $PROJECT_DIR" -u critical
        exit 1
    }

    python3 "$MAIN_SCRIPT" >> "$LOG_FILE" 2>&1 &
    local pid=$!
    disown "$pid" 2>/dev/null

    # Wait up to 3s for the PID file (written by Python on startup)
    for i in $(seq 1 10); do
        sleep 0.3
        if [ -f "$PID_FILE" ] && [ "$(cat "$PID_FILE")" = "$pid" ]; then
            # Python is alive and PID file matches — now wait for window
            for j in $(seq 1 5); do
                sleep 0.3
                local addr
                addr=$(find_window)
                if [ -n "$addr" ]; then
                    bring_to_front "$addr"
                    return 0
                fi
            done
            return 0
        fi
    done

    notify-send "$(basename "$0")" "⚠️ La ventana no apareció - revisa $LOG_FILE" -u critical
    return 1
}

# ── 5. Toggle (SIGUSR1 IPC — no hyprctl calls) ────────────────────────────

do_toggle() {
    local pid
    pid=$(get_saved_pid)

    if is_running "$pid"; then
        # Process exists → send SIGUSR1 for internal show/hide toggle
        kill -SIGUSR1 "$pid" 2>/dev/null
        return 0
    fi

    # Orphan: process alive but PID file was lost
    pid=$(find_orphan)
    if [ -n "$pid" ]; then
        echo "$pid" > "$PID_FILE"
        kill -SIGUSR1 "$pid" 2>/dev/null
        return 0
    fi

    # No process exists → launch fresh
    rm -f "$PID_FILE"
    do_launch
}

do_hide() {
    local pid
    pid=$(get_saved_pid)
    if is_running "$pid"; then
        kill -SIGUSR1 "$pid" 2>/dev/null
    fi
}

# ── 6. Main ───────────────────────────────────────────────────────────────

case "${1:-toggle}" in
    launch)  do_launch ;;
    hide)    do_hide ;;
    toggle|*) do_toggle ;;
esac
