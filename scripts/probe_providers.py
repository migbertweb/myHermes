#!/usr/bin/env python3
"""Benchmark opencode-go vs deepseek using direct HTTP calls with correct model names."""

import os
import sys
import time
import json
import urllib.request
import urllib.error

# Load env
ENV_PATH = os.path.expanduser("~/.hermes/.env")
env = {}
if os.path.exists(ENV_PATH):
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()

# ── Probe opencode-go base URL ──
# Try both possible URLs with a lightweight model first
def probe_opencode_go():
    api_key = env.get("OPENCODE_GO_API_KEY", "")
    if not api_key:
        return None, "No API key"
    
    # Try different base URLs and model names
    candidates = [
        ("https://opencode.ai/go/v1", "deepseek-v4-flash"),
        ("https://opencode.ai/zen/go/v1", "deepseek-v4-flash"),
        ("https://opencode.ai/v1", "deepseek-v4-flash"),
        ("https://opencode.ai/go/v1", "deepseek/deepseek-v4-flash"),
        ("https://opencode.ai/zen/go/v1", "deepseek/deepseek-v4-flash"),
    ]
    
    for base_url, model in candidates:
        url = f"{base_url.rstrip('/')}/chat/completions"
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": "Say 'hello'"}],
            "max_tokens": 10,
        }).encode("utf-8")
        
        req = urllib.request.Request(
            url, data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                return (base_url, model, data)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode(errors="replace")[:200]
            print(f"  ❌ {base_url} / {model} → HTTP {e.code}: {err_body}")
        except Exception as e:
            print(f"  ❌ {base_url} / {model} → {e}")
    return None, "All endpoints failed"

print("🔍 Probando endpoint de opencode-go...")
result = probe_opencode_go()
if result[0]:
    base_url, model, data = result
    print(f"  ✅ Encontrado: {base_url} / {model}")
    print(f"     Model usado: {data.get('model', '?')}")
else:
    print(f"  ❌ {result[1]}")

print("\n🔍 Probando DeepSeek directo...")
api_key = env.get("DEEPSEEK_API_KEY", "")
if api_key:
    for model_name in ["deepseek-chat", "deepseek-v4-flash"]:
        url = "https://api.deepseek.com/v1/chat/completions"
        body = json.dumps({
            "model": model_name,
            "messages": [{"role": "user", "content": "Say 'hello'"}],
            "max_tokens": 10,
        }).encode("utf-8")
        req = urllib.request.Request(
            url, data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
                print(f"  ✅ {model_name} → OK, model reported: {data.get('model', '?')}")
                break
        except urllib.error.HTTPError as e:
            err_body = e.read().decode(errors="replace")[:200]
            print(f"  ❌ {model_name} → HTTP {e.code}: {err_body}")
else:
    print("  ❌ No DEEPSEEK_API_KEY found")
