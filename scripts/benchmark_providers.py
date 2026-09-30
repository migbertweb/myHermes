#!/usr/bin/env python3
"""Benchmark two LLM providers with the same model and prompt."""

import os
import sys
import time
import json
import urllib.request
import urllib.error

# Load env manually from .hermes/.env
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

# ── Providers config ──
PROVIDERS = {
    "opencode-go": {
        "api_key": env.get("OPENCODE_GO_API_KEY", ""),
        "base_url": "https://opencode.ai/go/v1",
        "model": "deepseek-v4-flash",
    },
    "deepseek (directo)": {
        "api_key": env.get("DEEPSEEK_API_KEY", ""),
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",  # deepseek native model name
    },
}

PROMPT = """Escribe un párrafo de exactamente 5 líneas explicando qué es la entropía en termodinámica, en español claro y simple. No agregues nada más."""
MAX_TOKENS = 200
TEMPERATURE = 0.7

def call_provider(name, cfg):
    """Call a chat completion API and return timing + usage data."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {cfg['api_key']}",
    }
    body = json.dumps({
        "model": cfg["model"],
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "stream": False,
    }).encode("utf-8")

    url = f"{cfg['base_url'].rstrip('/')}/chat/completions"

    # Time the full request
    t0 = time.time()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        return {
            "provider": name,
            "error": f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}",
        }
    except urllib.error.URLError as e:
        return {
            "provider": name,
            "error": f"Connection error: {e.reason}",
        }
    total_time = time.time() - t0

    data = json.loads(raw)

    usage = data.get("usage", {})
    content = data["choices"][0]["message"]["content"] if data.get("choices") else ""

    # Approximate TTFT: can't measure exactly without streaming,
    # but we can note it's a non-streaming request
    chars_per_sec = len(content) / total_time if total_time > 0 else 0

    return {
        "provider": name,
        "model_used": data.get("model", cfg["model"]),
        "total_time_s": round(total_time, 2),
        "content_length_chars": len(content),
        "content_length_lines": len(content.strip().split("\n")),
        "chars_per_sec": round(chars_per_sec, 1),
        "input_tokens": usage.get("prompt_tokens", "N/A"),
        "output_tokens": usage.get("completion_tokens", "N/A"),
        "total_tokens": usage.get("total_tokens", "N/A"),
        "response_preview": content[:150].replace("\n", " | "),
        "error": None,
    }


results = []
for name, cfg in PROVIDERS.items():
    if not cfg["api_key"]:
        results.append({"provider": name, "error": "API key not found in .env"})
        continue
    print(f"\n⏳ Probando {name}...", flush=True)
    result = call_provider(name, cfg)
    results.append(result)
    if result.get("error"):
        print(f"  ❌ Error: {result['error']}")
    else:
        print(f"  ✅ {result['total_time_s']}s | {result['output_tokens']} tokens out | {result['input_tokens']} tokens in")

# ── Results table ──
print("\n" + "=" * 72)
print(f"{'PROVEEDOR':<22} {'TIEMPO':<10} {'TOKENS IN':<12} {'TOKENS OUT':<12} {'CHARS/s':<10}")
print("-" * 72)
for r in results:
    if r.get("error"):
        print(f"{r['provider']:<22} {'❌ '+r['error']}")
    else:
        print(f"{r['provider']:<22} {r['total_time_s']:<8}s {r['input_tokens']:<12} {r['output_tokens']:<12} {r['chars_per_sec']:<10}")
print("=" * 72)

# Price comparison (approximate, typical DeepSeek pricing)
print("\n💰 ESTIMACIÓN DE COSTOS (por 1M tokens):")
print(f"{'Proveedor':<22} {'Input':<14} {'Output':<14}")
print("-" * 50)
# DeepSeek official: $0.27/M input, $1.10/M output (approx)
# OpenCode Go: subscription-based, but per-token ~varies
print(f"{'opencode-go':<22} {'$0.27/M (est.)':<14} {'$1.10/M (est.)':<14}")
print(f"{'deepseek (directo)':<22} {'$0.27/M':<14} {'$1.10/M':<14}")
print("(DeepSeek directo tiene precios oficiales; opencode-go usa subscription $10/mes)")
