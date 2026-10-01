---
name: hermes-desktop-client
description: Build desktop GUI applications that communicate with Hermes Agent — floating windows, system tray apps, and custom widgets. Covers PyQt6 integration, Hyprland/Wayland floating-window conventions, and Hermes CLI oneshot communication.
---

# Hermes Desktop Client

Build desktop GUI applications that talk to Hermes Agent locally. These patterns work for floating AI-assistant windows, system tray chatbots, note-taking widgets, or any custom UI that needs to send prompts and receive responses.

## Hermes Communication Layer

The simplest and most reliable way for a desktop app to talk to Hermes is via the **oneshot CLI** (`hermes -z`). No server, no API key management in the client — just a subprocess call.

```python
import subprocess

def ask_hermes(text: str, session_id: str | None = None) -> str:
    cmd = ["hermes", "-z", text]
    if session_id:
        cmd.extend(["--resume", session_id])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.stdout.strip()
```

### Session Persistence

- Use `--resume <session_id>` to continue a conversation.
- Track the session ID by calling `hermes sessions list --json` after each message and taking the first result's `id`.
- Start fresh by omitting `--resume`.
- **Starting a completely new chat**: After clearing the UI and setting `session_id = None`, send a no-op (`hermes -z ""`) to let Hermes initialize a fresh session. Otherwise `_load_last_session()` may pick up a stale session from before the reset.

### Single Instance and IPC Toggle
For apps that need a reliable toggle (Show/Hide) without relying on external scripts or unstable signals, implement a `QLocalServer` within the app. 
- **Pattern**:
    1. Use `QLockFile` to detect if an instance is already running.
    2. If running, use `QLocalSocket` to send a `"toggle"` message to the existing server.
    3. The existing instance handles the connection in the main event loop and calls `window.toggle_visibility()`.
- **Pitfall**: Avoid `SIGUSR1` for GUI toggles; signals are asynchronous and can be unreliable or ignored by the Qt event loop. Sockets are the standard for robust IPC in PyQt6.
- **Implementation Detail**: When reading from `QLocalSocket`, use `bytes(conn.readAll().data()).decode()` to safely convert the `QByteArray` to a Python string.

  ```python
  def new_chat(self):
      self.hermes.session_id = None
      # ... clear chat UI widgets ...
      # Initialize a fresh Hermes session
      QTimer.singleShot(100, lambda: self.hermes.send_message(""))
  ```

### Limitations
- Each call is a full agent loop — expect 5-30s response times depending on the model.
- No streaming: you get the complete response at once. Show a "pensando..." indicator.
- `hermes -z` prints ONLY the final response to stdout (no banner, no tool previews).

## Two Approaches: WM-Managed vs App-Managed

Hermes desktop clients support two fundamentally different window styles. **Choose based on whether the user already has window manager rules (DMS/Hyprland config) that handle appearance.**

| Aspect | Standard Window (WM-Managed) | Floating Frameless (App-Managed) |
|---|---|---|
| Window decorations | System/WM-provided | Custom (frameless) |
| Opacity | WM handles (e.g. `opacity 0.92` in hyprland.conf) | App sets via `setWindowOpacity()` |
| Position/size | WM rules (`windowrulev2 = size`, `move`, `center`) | App calls `setGeometry()` / `center_on_screen()` |
| Pin/stay-on-top | WM rule (`windowrulev2 = pin`) | PyQt6 `WindowStaysOnTopHint` (⚠️ causes pinned issues) |
| System tray | Yes — close minimizes to tray | Optional (frameless with tray less common) |
| When to use | User has DMS or Hyprland window rules | You need a specific custom look (frosted glass, no borders) |

### Standard Window (WM-Managed) — Recommended for Hyprland/DMS users

The app does **not** set any window flags that interfere with the WM. The result is a plain QMainWindow whose appearance and behavior are fully controlled by Hyprland rules (or DMS fragments). This is the approach used by `agent-piro` and the `hermes-chat` project.

```python
from PyQt6.QtWidgets import QMainWindow, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Assistant")
        # NO FramelessWindowHint, NO WA_TranslucentBackground,
        # NO WindowStaysOnTopHint, NO setWindowOpacity.
        # The WM (Hyprland/DMS) handles all of that via window rules.

        self.setup_tray()   # required for close-to-tray behavior

    def closeEvent(self, event):
        # X button → minimize to tray, don't quit
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self._make_icon(), self)
        self.tray_icon.setToolTip("My Assistant")

        tray_menu = QMenu()
        show_action = tray_menu.addAction("Mostrar/Ocultar")
        show_action.triggered.connect(self.toggle_visibility)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Salir")
        quit_action.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(
            lambda reason: self.toggle_visibility()
            if reason == QSystemTrayIcon.ActivationReason.DoubleClick
            else None
        )
        self.tray_icon.show()

    def _make_icon(self):
        """Programmatic icon: no external image file needed."""
        from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(Qt.GlobalColor.darkCyan)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(2, 2, 60, 60, 12, 12)
        painter.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI", 28, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "VI")
        painter.end()
        return QIcon(pixmap)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
            self._input.setFocus()

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()
```

**Important:** With this approach, you MUST add `windowrulev2` entries in Hyprland (or let DMS manage them via `windowrules.conf`) to float, position, size, and optionally pin the window. The app itself is just a standard window — the WM transforms it into the floating overlay.

### Floating Frameless Window (App-Managed)

For a ChatGPT-macOS-style floating overlay where the app controls its own appearance, use these PyQt6 patterns:

### Window Setup

```python
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import Qt, QTimer

class FloatingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Assistant")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowOpacity(0.92)
        QTimer.singleShot(0, self._apply_geometry)

    def _apply_geometry(self):
        # Apply size AFTER the window is mapped (Hyprland compat)
        self.setFixedSize(420, 600)
        self.center_on_screen()

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.geometry()
            x = (geom.width() - 420) // 2
            y = (geom.height() - 600) // 2 - 60
            self.setGeometry(x, y, 420, 600)
```

### Key Points for Wayland/Hyprland

- **`QTimer.singleShot(0, fn)`** — critical. Hyprland may override initial geometry. Deferring `setFixedSize` to the next event loop tick ensures it sticks.
- **`WA_TranslucentBackground`** + **`setWindowOpacity()`** — enables the frosted glass look. Hyprland compositor renders the blur behind transparent areas.
- **Frameless + Tool flags** — removes window decorations so you can draw custom title bars and rounded corners.
- **`noinitialfocus`** — Hyprland rule to avoid stealing focus when spawning.
- **Drag support** — implement `mousePressEvent`/`mouseMoveEvent` for title-bar dragging (check `event.position().y() <= 40`).
- **⚠️ DO NOT use `WindowStaysOnTopHint`** — This flag causes Hyprland to set `pinned: true` on the window. A pinned window **cannot** be moved to a special workspace (`movetoworkspace special` is silently ignored). If you need stay-on-top behavior, use a Hyprland `windowrulev2 = pin, title:^(...)$` rule instead, and the toggle script will handle unpinning before hiding the window. If DMS manages the rules (see DMS pitfalls below), avoid PyQt6 `WindowStaysOnTopHint` entirely and let DMS control pinning.

### Frosted Glass via QSS

```python
self.setStyleSheet(f"""
    QFrame#central {{
        background: rgba(18, 18, 30, 0.75);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }}
""")
```

Use semi-transparent `rgba()` backgrounds. The more transparent, the more the Hyprland blur shows through.

### Chat Message Bubbles

Render messages in a scrollable `QWidget` with a `QVBoxLayout`. Each bubble is a `QFrame` containing a `QLabel`. Right-align user messages, left-align assistant. Use `QTextFormat.RichText` on labels for bold, italic, etc.

Focus management: after sending, scroll to bottom with `scrollArea.verticalScrollBar().setValue(sb.maximum())`.

## Hyprland Window Rules

Add rules in `~/.config/hypr/hyprland.conf` to make the window behave as a floating overlay. Rules vary depending on which approach you chose:

### For Standard Window (WM-Managed) — essential

Since the app does not set any window flags, these rules are **required** to make the window float and position it correctly:

```bash
windowrulev2 = float, title:^(Your App Title)$
windowrulev2 = noborder, title:^(Your App Title)$
windowrulev2 = size 420 600, title:^(Your App Title)$
windowrulev2 = center(1), title:^(Your App Title)$
windowrulev2 = dimaround, title:^(Your App Title)$
```

- `float` — transforms the standard window into an overlay (without this, it tiles like any normal app)
- `noborder` — removes window decorations for a cleaner look
- `size` + `center` — positions the window on the focused monitor
- `dimaround` — darkens the background behind the overlay

Optional extras:
```bash
windowrulev2 = opacity 0.92, title:^(Your App Title)$   # WM handles transparency
windowrulev2 = pin, title:^(Your App Title)$             # stays above other windows
windowrulev2 = noinitialfocus, title:^(Your App Title)$  # spawn without stealing focus
```

### For Floating Frameless (App-Managed)

The app already sets itself as frameless and translucent. Hyprland rules reinforce the behavior:

```bash
windowrulev2 = float, title:^(Your App Title)$
windowrulev2 = noborder, title:^(Your App Title)$
windowrulev2 = noinitialfocus, title:^(Your App Title)$
windowrulev2 = dimaround, title:^(Your App Title)$
windowrulev2 = center(1), title:^(Your App Title)$
```

- `dimaround` — darkens the background when the floating window is active (like ChatGPT macOS).
- `noborder` — since you draw your own rounded corners.
- `center(1)` — centers on the focused monitor.

## Directory Layout

Keep the project in a standalone directory (e.g. `~/hermes-chat/`):

```
~/hermes-chat/
├── main.py               # Entry point + UI
├── viernes-chat.sh       # Unified launch/toggle script
└── hyprland.conf         # Rules to source into Hyprland config
```

### Unified Launcher Script (Recommended)

Instead of separate `launch.sh` + `toggle.sh`, use a **single executable** that handles all three states: launch, toggle, and hide. Install it to `/usr/local/bin/` and bind `viernes-chat` (no path) in Hyprland.

Key improvements over separate scripts:
- **Robust PID validation** — checks `/proc/$PID/cmdline` so a recycled PID never tricks it
- **Dependency checking** — verifies `python3`, `PyQt6`, `hyprctl`, `jq` before launch
- **`nohup` + log redirection** — survives terminal closure
- **Special workspace toggle** — uses `movetoworkspace special:appname` to hide (not `togglefloating`, which breaks float-rule windows)
- **Window-gone detection** — if the process is running but the window disappeared (crash/close), automatically re-launches

```bash
#!/bin/bash
# ─── Unified Launcher / Toggle ─────────────────────────────────────────
# Usage:   viernes-chat          # toggle show/hide
#          viernes-chat launch   # force launch
#          viernes-chat hide     # force hide
#
# Bind in Hyprland: bind = SUPER, SPACE, exec, viernes-chat
# ────────────────────────────────────────────────────────────────────────

set -euo pipefail

PROJECT_DIR="$HOME/hermes-chat"
MAIN_SCRIPT="$PROJECT_DIR/main.py"
PID_FILE="$HOME/.cache/viernes-chat.pid"
WINDOW_TITLE="Viernes Chat"
LOG_FILE="$HOME/.cache/viernes-chat.log"

# ── 1. Dependency checks ──────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    notify-send "Viernes Chat" "❌ Python3 no está instalado" -u critical
    exit 1
fi
if ! python3 -c "import PyQt6" 2>/dev/null; then
    notify-send "Viernes Chat" "❌ PyQt6 no instalado\npip install PyQt6" -u critical
    exit 1
fi
if ! command -v hyprctl &>/dev/null; then
    notify-send "Viernes Chat" "❌ hyprctl no encontrado (¿Hyprland?)" -u critical
    exit 1
fi
if [ ! -f "$MAIN_SCRIPT" ]; then
    notify-send "Viernes Chat" "❌ No se encuentra $MAIN_SCRIPT" -u critical
    exit 1
fi

# ── 2. Robust PID validation ─────────────────────────────────────────────
# kill -0 alone is not enough — a recycled PID can produce false positives.
# Verify the process at that PID is actually our Python app.
is_running() {
    local pid="$1"
    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
        return 1
    fi
    if [ -d "/proc/$pid" ]; then
        local cmdline
        cmdline=$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || echo "")
        if [[ "$cmdline" == *"main.py"* ]]; then
            return 0
        fi
    fi
    return 1
}

# ── 3. Hyprland window management ───────────────────────────────────────
# Use special workspace for hide/show (NOT togglefloating — that breaks
# windows that already have the float window-rule).
get_window_address() {
    hyprctl clients -j | jq -r --arg title "$WINDOW_TITLE" \
        '.[] | select(.title == $title) | .address' | head -1
}

bring_to_front() {
    local addr="$1"
    hyprctl dispatch movetoworkspace "+1,address:$addr"
    hyprctl dispatch focuswindow "address:$addr"
}

hide_to_special() {
    local addr="$1"
    hyprctl dispatch movetoworkspace "special:viernes,address:$addr"
}

# ── 4. Launch / Toggle logic ─────────────────────────────────────────────
do_launch() {
    cd "$PROJECT_DIR"
    nohup python3 "$MAIN_SCRIPT" >> "$LOG_FILE" 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"

    # Wait up to 3s for the window to appear
    for i in $(seq 1 10); do
        sleep 0.3
        local addr; addr=$(get_window_address)
        if [ -n "$addr" ]; then
            bring_to_front "$addr"
            break
        fi
    done
}

do_toggle() {
    local pid; pid=$(get_saved_pid)
    local addr; addr=$(get_window_address)

    # Process exists but window is gone — restart silently
    if is_running "$pid" && [ -z "$addr" ]; then
        do_launch; return
    fi

    if [ -n "$addr" ]; then
        local mapped; mapped=$(hyprctl clients -j | jq -r --arg addr "$addr" \
            '.[] | select(.address == $addr) | .mapped')
        local active_addr; active_addr=$(hyprctl activewindow -j | jq -r '.address')
        if [ "$active_addr" = "$addr" ]; then
            hide_to_special "$addr"          # active → hide
        elif [ "$mapped" = "true" ]; then
            bring_to_front "$addr"           # visible but unfocused → focus
        else
            bring_to_front "$addr"           # in special → bring back
        fi
    elif is_running "$pid"; then
        notify-send "Viernes Chat" "⚠️ Running but window not found"
    else
        do_launch
    fi
}

case "${1:-toggle}" in
    launch)  do_launch ;;
    hide)    do_hide ;;
    *)       do_toggle ;;
esac
```

The `get_saved_pid()` helper reads the PID file:

```bash
get_saved_pid() {
    if [ -f "$PID_FILE" ]; then cat "$PID_FILE"; fi
}
```

The `do_hide()` action hides the window to the special workspace:

```bash
do_hide() {
    local addr; addr=$(get_window_address)
    [ -n "$addr" ] && hide_to_special "$addr"
}
```

These two helpers complete the unified script. The full, tested version is at `templates/toggle.sh` — prefer referencing or copying that file rather than re-assembling from the inline fragments above.

Install: `sudo cp viernes-chat.sh /usr/local/bin/viernes-chat && sudo chmod +x /usr/local/bin/viernes-chat`

Or install to `~/.local/bin/` (no sudo, already in user PATH on most distros):

```bash
cp viernes-chat.sh ~/.local/bin/viernes-chat
chmod +x ~/.local/bin/viernes-chat
```

Bind in Hyprland: `bind = SUPER, SPACE, exec, viernes-chat`

## Pitfalls

- **Hermes Gateway API Server requires `API_SERVER_KEY` even for loopback-only binds on 127.0.0.1** — the server refuses to start without it (`Refusing to start: API_SERVER_KEY is required for the API server, including loopback-only binds on 127.0.0.1.`). Use a hex key (`secrets.token_hex(16)`) to avoid the secret redaction system replacing it with `***` in terminal output and scripts.

- **Switching Hermes providers leaves a stale `base_url`** — When you run `hermes config set model.provider "newprovider"`, the old provider's `base_url` stays in `config.yaml`. Hermes merges it into the new provider config and keeps sending requests to the wrong endpoint. Always clear it: `hermes config set model.base_url ""`. Verify with `hermes config | grep -A5 "Model:"` — the endpoint URL should match the new provider, not the old one.

- **Telegram polling conflict after gateway restart** — If the gateway was previously running and you restart it (e.g. after config changes), Telegram sees two bot sessions and rejects the new one for ~30s (`Telegram polling conflict (1/5)`). Harmless — the gateway auto-retries — but noisy in logs. Avoid by stopping the old instance first and waiting a few seconds before starting the new one.

- **Hyprland overrides initial window size**: Always use `QTimer.singleShot(0)` to apply geometry after mapping. `setFixedSize` before `show()` may be ignored.
- **`WindowStaysOnTopHint` → Hyprland pins the window**: When PyQt6 sets `WindowStaysOnTopHint`, Hyprland marks the window as `pinned: true`. A pinned window **cannot** be moved to a special workspace (`movetoworkspace special` appears to succeed but the window stays put). If your toggle script uses special workspace for hide/show, either:
  - Remove `WindowStaysOnTopHint` from PyQt6 and pin via Hyprland rule instead, OR
  - Add `if is_pinned "$addr"; then hyprctl dispatch pin address:"$addr"; fi` before `movetoworkspace special`
- **DankMaterialShell (DMS) window rules can interfere**: If the user runs DMS, check `~/.config/hypr/dms/windowrules.conf` — it may apply its own rules (including `pin`, custom size, or `stayfocused`) for your window title. These rules are loaded after manual `hyprland.conf` and take precedence. DMS rule syntax: `windowrule = float 1, center off, match:title ^(Window Title)$, size WxH, move X Y, pin 1, animation slide`. To diagnose: `hyprctl clients -j | jq '.[] | select(.title == "Your Title") | {pinned, floating, workspace}'`. If `pinned: true` and you didn't set it, DMS is the culprit.
- **Multiple instances from rapid keybinding**: Hyprland executes the bind command on each keypress. If the toggle script doesn't finish before the next press, multiple instances can launch simultaneously. Use a lock file to serialize executions:
  ```bash
  LOCK_FILE="$HOME/.cache/myapp.lock"
  cleanup_lock() { rm -rf "$LOCK_FILE"; }
  trap cleanup_lock EXIT
  if ! mkdir "$LOCK_FILE" 2>/dev/null; then exit 0; fi
  ```
  `mkdir` is atomic on Linux — two concurrent scripts can't both succeed.
- **Multiple window titles after restarts**: The window title may vary between versions (e.g. "Viernes Chat" vs "hermes-chat" after a code change). The find-window helper should match against a list of known titles:
  ```bash
  WINDOW_TITLES=("Viernes Chat" "hermes-chat")
  find_window() {
      hyprctl clients -j | jq -r \
        'map(select(.title == "Viernes Chat" or .title == "hermes-chat")) | first | .address // ""'
  }
  ```
- **Multiple instances**: The `float` rule in Hyprland + repeated launches can create zombie windows. Use a PID file in `~/.cache/` to track the running instance. Validate the PID by checking `/proc/$PID/cmdline` — not just `kill -0` — to prevent false positives from recycled PIDs.
- **`noblur` conflicts with frosted glass**: If you set `noblur` in Hyprland rules, the translucent background won't show the compositor blur. Leave blur enabled.
- **`hyprctl clients` shows stale data**: After closing a window, there may be a brief delay before it disappears from the client list. Add `sleep 0.5` in toggle scripts if needed.
- **`setGeometry` vs `move`**: Use `setGeometry(x, y, w, h)` instead of separate `resize()` + `move()` calls for atomic positioning on Wayland.
- **DO NOT use `togglefloating` on float-ruled windows**: If a `windowrulev2 = float` rule exists, calling `hyprctl dispatch togglefloating` will *un-float* the window. Use `movetoworkspace special:<name>` to hide/show instead.
- **Background process dies when terminal closes**: Plain `python3 main.py &` without `nohup` receives SIGHUP when the spawning terminal exits. Always use `nohup python3 main.py >> log 2>&1 &` for keybind-launched processes.
- **Separate `launch.sh` + `toggle.sh` scripts confuse state**: Two scripts with overlapping PID logic inevitably diverge. Use a single unified script (see "Unified Launcher Script" above) that handles all three states: launch, toggle, and hide.
- **`eventFilter` + `QShortcut` for the same key**: Installing both a `QShortcut(QKeySequence("Return"))` and a key-press `eventFilter` that both call `send_message()` is redundant and can cause double-sends. Pick one: the eventFilter is preferred because it can also handle `Shift+Enter` for newline insertion.

  **Fix — use only the eventFilter:**

  ```python
  # Install the filter on the input field:
  self._input.installEventFilter(self)

  def eventFilter(self, obj, event):
      if obj == self._input and event.type() == event.Type.KeyPress:
          if event.key() == Qt.Key.Key_Return and not event.modifiers():
              self.send_message()
              return True  # stop propagation
          if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
              self._input.insertPlainText("\n")
              return True
      return super().eventFilter(obj, event)
  ```

  Remove any standalone `QShortcut(QKeySequence("Return"), self)` — it conflicts with the eventFilter and serves no purpose once the filter is installed.

- **QPainter icon requires `setPen(Qt.PenStyle.NoPen)` not `setBrush(Qt.GlobalColor.NoBrush)`**: When creating a programmatic tray icon with QPainter, use `painter.setPen(Qt.PenStyle.NoPen)` — `NoPen` is a pen style. The value `Qt.GlobalColor.NoBrush` is a brush style, and passing it to `setPen()` raises a `TypeError`.

  ```python
  # Correct:
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(Qt.GlobalColor.darkCyan)
  painter.drawRoundedRect(2, 2, 60, 60, 12, 12)

  # Wrong — TypeError:
  painter.setBrush(Qt.GlobalColor.NoBrush)
  ```

- **Close-to-tray requires overriding `closeEvent`**: By default, clicking the X button on a QMainWindow calls `closeEvent()` which destroys the window and exits QApplication. For a tray-based app, override `closeEvent` to hide instead:

  ```python
  def closeEvent(self, event):
      if self.tray_icon and self.tray_icon.isVisible():
          self.hide()
          event.ignore()
      else:
          event.accept()
  ```

  Without this, closing the window also kills the background process — the tray icon vanishes and the app is gone. To truly quit (e.g. from a "Salir" menu action), call `self.tray_icon.hide()` first, then `QApplication.quit()`.

## Linked Files

This skill includes reusable assets:

| File | Purpose |
|------|---------|
| `templates/toggle.sh` | Unified launch/toggle/hide script — single Hyprland keybind entry point with dependency checks, lock file, pin handling, and special-workspace hiding |
| `templates/launch.sh` | Minimal launch script (start or refocus) — less robust than toggle.sh, kept for simpler use cases |

