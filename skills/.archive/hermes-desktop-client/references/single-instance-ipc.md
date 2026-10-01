# Single Instance Toggle via QLocalServer

This reference documents the implementation of a single-instance window that can be toggled (shown/hidden) by launching the application again.

## Architecture
1. **Locking**: A `QLockFile` in `/tmp/` ensures only one process is the "owner".
2. **Server**: The owner process starts a `QLocalServer` listening on a unique name (e.g., `myapp-single-instance`).
3. **Client**: When a second process starts, it fails to get the lock, connects to the `QLocalServer` via `QLocalSocket`, sends a "toggle" string, and immediately exits.
4. **Action**: The owner process receives the connection and triggers `window.show()` / `window.hide()`.

## Code Snippet (PySide6/PyQt6)

```python
# --- In main.py ---
LOCK_FILE = Path("/tmp/myapp.lock")
SERVER_NAME = "myapp-single-instance"

def _send_toggle():
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if socket.waitForConnected(1000):
        socket.write(b"toggle")
        socket.waitForBytesWritten(1000)
        return True
    return False

def main():
    lock = QLockFile(str(LOCK_FILE))
    if not lock.tryLock(100):
        if _send_toggle(): return
        lock.unlock()

    app = QApplication(sys.argv)
    QLocalServer.removeServer(SERVER_NAME)
    server = QLocalServer()
    server.listen(SERVER_NAME)
    
    window = MyWindow()
    
    def _handle_connection():
        conn = server.nextPendingConnection()
        if conn and conn.waitForReadyRead(1000):
            data = bytes(conn.readAll().data()).decode().strip()
            if data == "toggle":
                window.toggle_visibility()
            conn.disconnectFromServer()
            
    server.newConnection.connect(_handle_connection)
    window.show()
    sys.exit(app.exec())
```

## Pitfalls
- **Zombie Servers**: Always call `QLocalServer.removeServer(SERVER_NAME)` before `listen()` to clear stale sockets from previous crashes.
- **Threading**: The `_handle_connection` must run in the main GUI thread (which `newConnection.connect` does by default) to manipulate window visibility.
- **QByteArray conversion**: Directly calling `bytes()` on `readAll()` can fail in some PySide6 versions; use `.data()` first.
