#!/usr/bin/env python3
"""Verify remote Ollama accessibility from Hermes server.

Usage:
    python3 verify-remote-ollama.py <HOST> [PORT]

Example:
    python3 verify-remote-ollama.py 192.168.1.17 11434
"""

import json, socket, sys, urllib.request, urllib.error

HOST = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.17"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 11434
BASE = f"http://{HOST}:{PORT}"

def ok(msg):
    print(f"  ✅ {msg}")

def fail(msg, detail=""):
    print(f"  ❌ {msg}" + (f" — {detail}" if detail else ""))

def check_tcp():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    try:
        s.connect((HOST, PORT))
        s.close()
        ok(f"TCP port {PORT} reachable on {HOST}")
        return True
    except Exception as e:
        fail(f"TCP port {PORT} NOT reachable on {HOST}", e)
        return False

def check_api(path, label):
    try:
        r = urllib.request.urlopen(f"{BASE}{path}", timeout=5)
        data = json.loads(r.read())
        ok(f"{label} endpoint responds")
        return data
    except Exception as e:
        fail(f"{label} endpoint failed", e)
        return None

print(f"\n🔍 Verifying Ollama at {BASE}\n")

if check_tcp():
    tags = check_api("/api/tags", "Ollama API")
    if tags:
        models = tags.get("models", [])
        if models:
            ok(f"{len(models)} model(s) installed:")
            for m in models:
                print(f"     - {m['name']}")
        else:
            fail("No models installed — run: ollama pull <model>")

    v1 = check_api("/v1/models", "OpenAI-compatible")
    if v1:
        models = v1.get("data", [])
        if models:
            ok("OpenAI-compatible models advertised:")
            for m in models:
                print(f"     - {m['id']}")

    # Quick inference test
    try:
        req = urllib.request.Request(
            f"{BASE}/api/generate",
            data=json.dumps({"model": "llama3.2:1b", "prompt": "Say hello", "stream": False}).encode(),
            headers={"Content-Type": "application/json"},
        )
        r = urllib.request.urlopen(req, timeout=30)
        result = json.loads(r.read())
        if result.get("response"):
            ok("Inference works (llama3.2:1b responds)")
        else:
            fail("Inference returned empty response")
    except Exception as e:
        fail("Inference test failed", e)

print()
