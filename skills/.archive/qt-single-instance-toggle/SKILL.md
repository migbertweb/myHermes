---
name: qt-single-instance-toggle
description: Implementation of a single-instance PySide6 application with a remote visibility toggle mechanism using QLocalServer and QLockFile.
---

# Qt-based Desktop Application Single-Instance Toggle

This skill provides a proven workflow for creating PySide6/PyQt6 applications that maintain a single instance and support a "toggle visibility" mechanism (show/hide) triggered by an external process or signal.

## Implementation Pattern

To achieve a single-instance toggle, the application must implement both a locking mechanism (to prevent duplicates) and an Inter-Process Communication (IPC) channel (to tell the existing instance to show/hide).

### 1. The Locking & IPC Mechanism (`main.py`)
Use `QLockFile` to detect if the app is already running and `QLocalServer`/`QLocalSocket` for communication.

**Workflow:**
1. Attempt to acquire a `QLockFile` in `/tmp/`.
2. If the lock fails:
   - Create a `QLocalSocket`.
   - Connect to a unique server name (e.g., `app-name-single-instance`).
   - Send a trigger string (e.g., `"toggle"`).
   - Exit the second process immediately.
3. If the lock succeeds:
   - Initialize `QApplication`.
   - Start a `QLocalServer` listening on the unique server name.
   - Connect `newConnection` to a handler that reads the socket data and calls the window's `toggle_visibility()` method.

### 2. The Visibility Toggle (`widget.py`)
The window should implement a method to switch between visible and hidden states without closing.

```python
def toggle_visibility(self):
    if self.isVisible() and not self.isMinimized():
        self.hide()
    else:
        self.show()
        self.raise_()
        self.activateWindow()
```

## Pitfalls & Lessons Learned

### ⚠️ Avoid SIGUSR1 for Qt Toggles
Using `signal.signal(signal.SIGUSR1, ...)` to trigger UI changes is fragile. Signals are asynchronous and can interrupt the main thread at unsafe moments. **Prefer `QLocalServer` for a deterministic and thread-safe approach.**

### ⚠️ QByteArray to String Conversion
In PySide6, `conn.readAll()` returns a `QByteArray`. Converting this directly to bytes can sometimes trigger type errors.
- **Incorrect**: `bytes(conn.readAll()).decode()`
- **Correct**: `bytes(conn.readAll().data()).decode().strip()`

### ⚠️ Resolving Binaries in GUI Subprocesses
Applications launched from window manager binds (e.g., Hyprland) or desktop launchers do **not** inherit the full user `PATH` (often missing `~/.local/bin`). 
- **Pitfall**: `subprocess.run(["my-cli-tool"])` will raise `FileNotFoundError` even if it works in the terminal.
- **Fix**: Always resolve the executable path explicitly:
  ```python
  import shutil
  import os
  CMD_PATH = os.environ.get("MY_TOOL") or shutil.which("my-tool") or "/home/user/.local/bin/my-tool"
  subprocess.run([CMD_PATH, "arg"])
  ```

### ⚠️ Palette Forcing (Dark Mode)
Simply setting a CSS `background-color` on `QMainWindow` often leaves menus and tooltips in "Light Mode". To force a true dark theme:
1. Define a `QPalette`.
2. Use `QPalette.ColorRole` (e.g., `QPalette.ColorRole.Window`, `QPalette.ColorRole.Base`).
3. Apply it globally via `QApplication.setPalette(palette)`.

## Verification Steps
1. Run the app $\rightarrow$ Window opens.
2. Run the app again in a new terminal $\rightarrow$ Existing window should hide.
3. Run the app a third time $\rightarrow$ Existing window should reappear.
