# SIGUSR1 IPC for Single-Instance Toggle

An alternative to Hyprland's `movetoworkspace special` for hiding/showing a window. The **Python process** manages visibility internally via a Unix signal, making toggle reliable regardless of window manager rules, pin state, or DMS interference.

## Architecture

```
┌──────────────┐     SIGUSR1     ┌──────────────────────┐
│  viernes-chat │ ──────────────► │  main.py (PyQt6)      │
│  (bash script) │                │                        │
│                │                │  QTimer polls flag     │
│  kill -USR1    │                │  every 150ms            │
│  $PID          │                │                        │
│                │                │  toggle_visibility()   │
└──────────────┘                │  (hide/show from Qt)   │
                                  └──────────────────────┘
```

**Why this works better than hyprctl-based toggle:**

| Approach | Problem | Solution |
|---|---|---|
| `hyprctl dispatch movetoworkspace special` | Fails silently on pinned windows (Hyprland refuses to move pinned windows to special workspaces) | Python's `hide()` doesn't care about pin — it just stops painting the window |
| `hyprctl clients -j` to find window | Race condition if window is being mapped/unmapped; stale client list | No external window detection needed — the process knows its own state |
| DMS windowrules conflict | DMS may re-apply `pin` or `float` after toggle, breaking state | No DMS interaction — Python directly controls visibility |
| Multiple window titles | Window title might change between launches | No title matching — PID file + orphan detection handle identity |

## Python Side: Qt-Compatible Signal Handler

Qt does NOT allow GUI operations (hide/show) from signal handlers. The safe pattern:

```python
import signal

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._toggle_requested = False
        self._setup_signal_handler()

    def _setup_signal_handler(self):
        # Signal handler ONLY sets a flag — never calls Qt methods
        signal.signal(signal.SIGUSR1, lambda s, f: setattr(self, '_toggle_requested', True))

        # QTimer in main thread polls the flag
        self._toggle_timer = QTimer(self)
        self._toggle_timer.timeout.connect(self._check_toggle_signal)
        self._toggle_timer.start(150)  # 150ms polling

    def _check_toggle_signal(self):
        if self._toggle_requested:
            self._toggle_requested = False
            self.toggle_visibility()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            self._input.setFocus()
```

Key details:
- **150ms polling** is imperceptible latency and avoids flooding the event loop
- The signal handler (`lambda s, f`) is thread-safe because it only writes to a Python bool
- The QTimer runs in Qt's main thread where `hide()`/`show()` are safe

## Bash Side: Script Changes

The bash script no longer calls `hyprctl` for toggle. It just reads the PID and sends a signal:

```bash
# ~/.local/bin/viernes-chat (simplified toggle)

do_toggle() {
    local pid
    pid=$(get_saved_pid)

    if is_running "$pid"; then
        # Process exists → send SIGUSR1 to toggle
        kill -SIGUSR1 "$pid" 2>/dev/null
        return 0
    fi

    # Orphan detection: find a main.py process without PID file
    pid=$(find_orphan)
    if [ -n "$pid" ]; then
        echo "$pid" > "$PID_FILE"
        kill -SIGUSR1 "$pid" 2>/dev/null
        return 0
    fi

    # No process → launch
    rm -f "$PID_FILE"
    do_launch
}
```

The `find_orphan()` function:

```bash
find_orphan() {
    local pids
    pids=$(pgrep -f 'python3.*/home/.*/main\.py' 2>/dev/null | grep -v -e '^$$\|grep\|viernes-chat' || true)
    for pid in $pids; do
        if [ -r "/proc/$pid/cmdline" ] && grep -q 'main\.py' "/proc/$pid/cmdline" 2>/dev/null; then
            echo "$pid"
            return 0
        fi
    done
    return 1
}
```

## Full flow

1. **First call** (`viernes-chat`): No PID file, no orphan → `do_launch()` starts Python → Python writes PID file → window appears
2. **Second call** (`viernes-chat`): PID file found, process alive → `kill -SIGUSR1 $PID` → `toggle_visibility()` hides window
3. **Third call** (`viernes-chat`): Same PID, SIGUSR1 → `toggle_visibility()` shows window
4. **PID file lost, process alive** → `find_orphan()` detects it, rewrites PID file, sends SIGUSR1

## Pitfalls

- **Do NOT call Qt methods inside `signal.signal()` handlers.** Qt is not signal-safe. The flag+QTimer pattern is mandatory.
- **SIGUSR1 is process-wide.** If you have threads, only the main thread receives the signal by default. Qt runs on the main thread, so this is fine.
- **Lock file prevents concurrent launches.** Pair `do_launch()` with `mkdir LOCK_FILE` (atomic) to prevent rapid keybinding from spawning multiple processes.
- **`/proc/PID/cmdline` vs `kill -0`.** Always check `/proc/PID/cmdline` for PID validation — `kill -0` returns success for any live PID, even if it's a different process that recycled the number.
