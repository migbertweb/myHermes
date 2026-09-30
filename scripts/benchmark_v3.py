#!/usr/bin/env python3
"""Benchmark opencode-go vs deepseek (directo) for deepseek-v4-flash model."""

import os
import time
import json
import urllib.request
import urllib.error

PROMPT = """Escribe exactamente 3 líneas sobre la teoría de la relatividad de Einstein en español, explicado para niños de 10 años. No agregues introducciones ni despedidas, solo las 3 líneas."""

def call_api(url, api_key, model):
    """Call chat completion API and return timing + usage."""
    base = url.rstrip("/")
    if not base.endswith("/v1"):
        base += "/v1"
    full_url = f"{base}/chat/completions"

    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 300,
        "temperature": 0.7,
        "stream": False,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    req = urllib.request.Request(full_url, data=body, headers=headers, method="POST")
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=90) as resp:
        raw = resp.read()
    elapsed = time.time() - t0

    data = json.loads(raw)
    usage = data.get("usage", {})
    content = data["choices"][0]["message"]["content"] if data.get("choices") else ""
    model_reported = data.get("model", "?")

    return {
        "time_s": round(elapsed, 3),
        "input_tokens": usage.get("prompt_tokens", "?"),
        "output_tokens": usage.get("completion_tokens", "?"),
        "total_tokens": usage.get("total_tokens", "?"),
        "content_preview": content[:100].replace("\n", " | "),
        "model_reported": model_reported,
    }


PROVIDERS = [
    {
        "label": "opencode-go",
        "url": "https://opencode.ai/zen/go",
        "env_key": "OPENCODE_GO_API_KEY",
        "model": "deepseek-v4-flash",
    },
    {
        "label": "deepseek (directo)",
        "url": "https://api.deepseek.com",
        "env_key": "DEEPSEEK_API_KEY",
        "model": "deepseek-chat",
    },
]

# Get API keys from environment
for p in PROVIDERS:
    p["api_key"] = os.environ.get(p["env_key"], "")

print("=" * 72)
print("  BENCHMARK: opencode-go vs deepseek (directo)")
print("  Modelo: deepseek-v4-flash")
print("  3 corridas por proveedor con el mismo prompt")
print("=" * 72)

results = []

for p in PROVIDERS:
    if not p["api_key"]:
        print(f"\n❌ {p['label']}: No se encontró {p['env_key']} en el entorno")
        continue

    print(f"\n📡 {p['label']} ({p['model']})")
    print("-" * 50)

    times = []
    in_toks = []
    out_toks = []
    content_previews = []

    for i in range(3):
        try:
            r = call_api(p["url"], p["api_key"], p["model"])
            times.append(r["time_s"])
            in_toks.append(r["input_tokens"])
            out_toks.append(r["output_tokens"])
            content_previews.append(r["content_preview"])
            status = "✅"
        except urllib.error.HTTPError as e:
            err_body = e.read().decode(errors="replace")[:150]
            status = f"❌ HTTP {e.code}: {err_body}"
        except urllib.error.URLError as e:
            status = f"❌ Connection: {e.reason}"
        except Exception as e:
            status = f"❌ {e}"

        print(f"  Run {i+1}: {status}")
        if "time_s" in locals() and i < len(times):
            print(f"         {r['time_s']}s · {r['input_tokens']} in → {r['output_tokens']} out")
            print(f"         modelo reportado: {r['model_reported']}")

        time.sleep(0.5)

    if times:
        avg = sum(times) / len(times)
        results.append({
            "label": p["label"],
            "avg_time": round(avg, 3),
            "min_time": round(min(times), 3),
            "max_time": round(max(times), 3),
            "avg_in": sum(t for t in in_toks if isinstance(t, int)) // max(len([t for t in in_toks if isinstance(t, int)]), 1),
            "avg_out": sum(t for t in out_toks if isinstance(t, int)) // max(len([t for t in out_toks if isinstance(t, int)]), 1),
            "sample": content_previews[0] if content_previews else "",
        })

# Comparison table
print("\n" + "=" * 72)
print("  R E S U L T A D O S")
print("=" * 72)
print(f"{'PROVEEDOR':<22} {'PROMEDIO':<12} {'MÍN':<10} {'MÁX':<10} {'TOK IN':<10} {'TOK OUT':<10}")
print("-" * 72)
for r in results:
    print(f"{r['label']:<22} {r['avg_time']:<10}s {r['min_time']:<8}s {r['max_time']:<8}s {r['avg_in']:<10} {r['avg_out']:<10}")
    print(f"{'':22} 🎯 {r['sample'][:80]}")
print("=" * 72)

# Cost analysis
print("\n💰 ANÁLISIS DE COSTOS")
print("-" * 72)
print(f"{'opencode-go':<22} $10/mes suscripción fija (sin límite)")
print(f"{'deepseek directo':<22} $0.27/M input | $1.10/M output (pay-as-you-go)")
print()
avg_in_total = sum(r.get("avg_in", 0) for r in results)
avg_out_total = sum(r.get("avg_out", 0) for r in results)
print(f"(Esta consulta: ~{results[0].get('avg_in', '?')}M in + ~{results[0].get('avg_out', '?')}M out sería ~$0.0000XX en DeepSeek)")
print()
if len(results) >= 2:
    t1 = results[0]["avg_time"]
    t2 = results[1]["avg_time"]
    faster = results[0]["label"] if t1 < t2 else results[1]["label"]
    diff_pct = abs(t1 - t2) / max(t1, t2) * 100
    print(f"⚡ Más rápido: {faster} ({diff_pct:.0f}% de diferencia en promedio)")
print("=" * 72)
