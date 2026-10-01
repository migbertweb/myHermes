#!/usr/bin/env python3
"""Test ACP TCP bridge connectivity from laptop to server.

Usage:
  ./test-acp-connection.py
  # Expect: "✅ Server accessible via ACP on port 8000"
"""
import socket
import sys

SERVER_HOST = '192.168.1.8'
SERVER_PORT = 8000


def main():
    s = socket.socket()
    s.settimeout(5)
    try:
        s.connect((SERVER_HOST, SERVER_PORT))
        s.sendall(b'{"jsonrpc":"2.0","method":"ping","id":1}\n')
        import time
        time.sleep(0.5)
        data = s.recv(4096)
        if data:
            print(f"✅ Server accessible via ACP on port {SERVER_PORT}")
            print(f"   Response: {data[:100]}")
        else:
            print(f"⚠️  Connected but no response")
        s.close()
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
