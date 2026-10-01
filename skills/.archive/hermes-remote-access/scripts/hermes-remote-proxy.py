#!/usr/bin/env python3
"""Hermes ACP Remote Proxy — Laptop Side

Connects to the server's Hermes ACP TCP bridge and forwards stdio ↔ TCP,
so the VS Code extension thinks it's running hermes acp locally.

Usage:
  chmod +x hermes-remote-proxy.py
  # Set VS Code setting: "hermes.path": "/path/to/hermes-remote-proxy.py"

Environment variables (optional):
  HERMES_SERVER_HOST  — default: 192.168.1.8
  HERMES_SERVER_PORT  — default: 8000
"""

import os
import select
import socket
import sys

SERVER_HOST = os.environ.get("HERMES_SERVER_HOST", "192.168.1.8")
SERVER_PORT = int(os.environ.get("HERMES_SERVER_PORT", "8000"))


def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    try:
        sock.connect((SERVER_HOST, SERVER_PORT))
    except OSError as e:
        print(f"Error connecting to {SERVER_HOST}:{SERVER_PORT}: {e}",
              file=sys.stderr)
        sys.exit(1)

    sock.settimeout(None)

    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)
    poll.register(sock, select.POLLIN)

    stdin_fd = sys.stdin.fileno()
    sock_fd = sock.fileno()

    try:
        while True:
            events = poll.poll(500)
            for fd, event in events:
                if event & select.POLLIN:
                    if fd == stdin_fd:
                        data = os.read(stdin_fd, 65536)
                        if not data:
                            return
                        sock.sendall(data)
                    elif fd == sock_fd:
                        data = sock.recv(65536)
                        if not data:
                            return
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()
                elif event & (select.POLLHUP | select.POLLERR | select.POLLNVAL):
                    return
    except (BrokenPipeError, ConnectionError):
        pass
    except KeyboardInterrupt:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
